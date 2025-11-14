import csv
from io import StringIO
from pathlib import Path
from typing import List
from uuid import UUID
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


from app.core.cache import RedisCache
from app.core.deps import get_cache_client, get_current_active_user, get_db, get_user_id
from app.schemas.resume import (
    ResumeList,
    ResumeParseResponse,
    ResumeRead,
    ResumeUpdate,
    ResumeUploadResponse,
)
from app.services.resume_service import ResumeService
from app.utils.file_upload import delete_file, save_uploaded_file
from app.services.batch_service import BatchService
from app.schemas.batch import BatchUploadResponse
from common.logging import get_logger
from app.utils.embedding_generator import get_cache_info
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate


router = APIRouter()
logger = get_logger(__name__)


# Helper to unwrap experience and education from dict wrappers
def unwrap_resume_fields(resume):
    experience_list = []
    if resume.experience:
        if isinstance(resume.experience, dict) and "entries" in resume.experience:
            experience_list = resume.experience["entries"]
        elif isinstance(resume.experience, list):
            experience_list = resume.experience

    education_list = []
    if resume.education:
        if isinstance(resume.education, dict) and "entries" in resume.education:
            education_list = resume.education["entries"]
        elif isinstance(resume.education, list):
            education_list = resume.education

    # Create resume dict with unwrapped lists
    resume_dict = resume.__dict__.copy()
    resume_dict["experience"] = experience_list
    resume_dict["education"] = education_list

    return resume_dict


# Debug Endpoints


@router.get("/debug/model-cache")
async def debug_model_cache():

    cache_info = get_cache_info()

    return {
        "cache_status": "cached" if cache_info["is_cached"] else "not cached",
        "model": cache_info["model_name"],
        "load_time_seconds": cache_info["load_time"],
        "memory_mb": cache_info["estimated_memory_mb"],
        "recommendation": (
            "Model is cached and ready"
            if cache_info["is_cached"]
            else "Model will be loaded on first use"
        ),
    }


@router.get("/debug/websocket-connections")
async def debug_websocket_connections(
    current_user: dict = Depends(get_current_active_user),
):

    from app.core.websocket import connected_users

    return {
        "total_users": len(connected_users),
        "connections": {
            user_id: list(sids) for user_id, sids in connected_users.items()
        },
        "your_user_id": current_user["sub"],
    }


# Stats and export endpoints


@router.get("/stats")
async def get_resume_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
):

    resume_service = ResumeService(db)

    # Get counts
    total = await resume_service.count_resumes(user_id)

    # Get parsed count
    parsed = await db.execute(
        select(func.count(Resume.id)).where(
            Resume.user_id == user_id,
            Resume.is_parsed == True,
            Resume.is_deleted == False,
        )
    )
    parsed_count = parsed.scalar() or 0

    embedded = await db.execute(
        select(func.count(Resume.id)).where(
            Resume.user_id == user_id,
            Resume.is_embedding_generated == True,
            Resume.is_deleted == False,
        )
    )
    embedded_count = embedded.scalar() or 0

    return {
        "total_resumes": total,
        "parsed_resumes": parsed_count,
        "with_embeddings": embedded_count,
        "parsing_rate": round(parsed_count / total * 100, 1) if total > 0 else 0,
        "embedding_rate": round(embedded_count / total * 100, 1) if total > 0 else 0,
    }


@router.get("/export/csv")
async def export_all_resumes_csv(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
):

    resume_service = ResumeService(db)

    # Get all user's resumes
    resumes = await resume_service.get_resumes_by_user(user_id, skip=0, limit=1000)

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "ID",
            "Name",
            "Email",
            "Phone",
            "Location",
            "Experience (Years)",
            "Skills Count",
            "Education Count",
            "Parsed",
            "Created At",
            "Filename",
        ]
    )

    # Data
    for resume in resumes:
        skills_count = 0
        if resume.skills:
            if isinstance(resume.skills, dict):
                skills_count = sum(len(s) for s in resume.skills.values())
            elif isinstance(resume.skills, list):
                skills_count = len(resume.skills)

        # Handle dict wrapper
        edu_count = 0
        if resume.education:
            if isinstance(resume.education, dict) and "entries" in resume.education:
                edu_count = len(resume.education["entries"])
            elif isinstance(resume.education, list):
                edu_count = len(resume.education)

        writer.writerow(
            [
                str(resume.id),
                resume.full_name or "",
                resume.email or "",
                resume.phone or "",
                resume.location or "",
                resume.total_experience_years or 0,
                skills_count,
                edu_count,
                "Yes" if resume.is_parsed else "No",
                resume.created_at.isoformat() if resume.created_at else "",
                resume.filename,
            ]
        )

    csv_content = output.getvalue()
    output.close()

    # Return as downloadable file
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=my_resumes_export.csv"},
    )


# Batch upload


@router.post("/batch", response_model=BatchUploadResponse)
async def batch_upload_resumes(
    files: List[UploadFile] = File(
        ..., description="Resume files to upload - Upto 10 Files"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user["sub"])

    logger.info(f"Batch upload request: {len(files)} files from user {user_id}")

    # Go up 5 levels to reach resume_parser_service/ directory
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    upload_dir = base_dir / "uploads"

    logger.info(f"Upload directory: {upload_dir}")

    # Process batch
    batch_service = BatchService(db)
    response = await batch_service.batch_upload_resumes(
        files=files,
        user_id=user_id,
        upload_dir=upload_dir,
    )

    return response


# Resume CRUD Operations


@router.post(
    "/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or DOC)"),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache_client),
):

    # Save file
    file_path, file_size = await save_uploaded_file(file, user_id)

    # Get file extension
    file_extension = file.filename.split(".")[-1].lower()

    # Create resume entry in database
    resume_service = ResumeService(db)

    resume_data = ResumeCreate(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_extension,
    )

    resume = await resume_service.create_resume(resume_data)

    await resume_service.parse_resume(resume.id, use_ocr=False)

    # Clear search cache for user after upload
    await cache.clear_user_cache(str(user_id))
    logger.info(f"Cleared search cache for user {user_id} after upload")

    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=resume.filename,
        file_size=resume.file_size,
        message="Resume uploaded successfully",
        status="uploaded",
    )


@router.post("/{resume_id}/parse", response_model=ResumeParseResponse)
async def parse_resume(
    resume_id: UUID,
    use_ocr: bool = Query(default=False, description="Use OCR for scanned documents"),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):

    try:
        resume_service = ResumeService(db)
        parsed_data = await resume_service.parse_resume(resume_id, use_ocr)

        return ResumeParseResponse(
            resume_id=resume_id,
            message="Resume parsed successfully",
            status="parsed",
            parsed_data=parsed_data.model_dump(),
        )

    except Exception as e:
        logger.error(f"Parse error: {str(e)}")
        return ResumeParseResponse(
            resume_id=resume_id,
            message="Failed to parse resume",
            status="error",
            parsed_data=None,
            error=str(e),
        )


@router.get("/{resume_id}/preview")
async def get_resume_preview(
    resume_id: UUID,
    lines: int = Query(default=10, ge=5, le=50, description="Number of lines"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
):

    resume_service = ResumeService(db)
    resume = await resume_service.get_resume_by_id(resume_id)

    if not resume:
        raise HTTPException(404, "Resume not found")

    if resume.user_id != user_id:
        raise HTTPException(403, "Not authorized")

    # Get first N lines
    if resume.raw_text:
        all_lines = resume.raw_text.split("\n")
        preview_lines = all_lines[:lines]
        total_lines = len(all_lines)
    else:
        preview_lines = []
        total_lines = 0

    return {
        "resume_id": resume_id,
        "filename": resume.filename,
        "total_lines": total_lines,
        "preview_lines": preview_lines,
        "has_more": total_lines > lines,
    }


@router.get("", response_model=ResumeList)
async def list_resumes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):

    resume_service = ResumeService(db)

    resumes = await resume_service.get_resumes_by_user(user_id, skip=skip, limit=limit)
    total = await resume_service.count_resumes(user_id)

    total_pages = (total + limit - 1) // limit

    # Unwrap experience and education for each resume
    unwrapped_resumes = []
    for resume in resumes:
        try:
            resume_dict = unwrap_resume_fields(resume)
            unwrapped_resumes.append(ResumeRead.model_validate(resume_dict))
        except Exception as e:
            logger.error(f"Error processing resume {resume.id}: {e}")
            # Skip problematic resumes
            continue

    return ResumeList(
        resumes=unwrapped_resumes,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    resume_service = ResumeService(db)

    resume = await resume_service.get_resume_by_id(resume_id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )

    if resume.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resume",
        )

    resume_dict = unwrap_resume_fields(resume)
    return ResumeRead.model_validate(resume_dict)


@router.patch("/{resume_id}", response_model=ResumeRead)
async def update_resume(
    resume_id: UUID,
    resume_update: ResumeUpdate,
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):

    resume_service = ResumeService(db)

    # Check if resume exists and belongs to user
    resume = await resume_service.get_resume_by_id(resume_id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )

    if resume.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this resume",
        )

    # Update resume
    updated_resume = await resume_service.update_resume(resume_id, resume_update)

    resume_dict = unwrap_resume_fields(updated_resume)
    return ResumeRead.model_validate(resume_dict)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    hard_delete: bool = Query(default=False, description="Permanently delete"),
    current_user: dict = Depends(get_current_active_user),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache_client),
):

    resume_service = ResumeService(db)

    # Check if resume exists and belongs to user
    resume = await resume_service.get_resume_by_id(resume_id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )

    if resume.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this resume",
        )

    # Delete resume
    await resume_service.delete_resume(resume_id, hard_delete=hard_delete)

    # Delete file if hard delete
    if hard_delete:
        delete_file(resume.file_path)

    # Clear search cache after deletion
    await cache.clear_user_cache(str(user_id))
    logger.info(f"Cleared search cache for user {user_id} after deletion")
