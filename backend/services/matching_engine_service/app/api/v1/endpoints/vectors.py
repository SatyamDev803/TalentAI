from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
from uuid import UUID

from app.services.vector_sync_service import vector_sync_service
from app.core.deps import get_db
from app.schemas.vector import (
    VectorSyncRequest,
    VectorSyncResponse,
    ConsistencyCheckResponse,
)
from common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Sync
@router.post("/sync/resume/{resume_id}", response_model=VectorSyncResponse)
async def sync_resume_vectors(
    resume_id: UUID, request: VectorSyncRequest, db: AsyncSession = Depends(get_db)
):

    try:
        success = await vector_sync_service.sync_resume(
            db=db,
            resume_id=str(resume_id),
            resume_text=request.content,
            metadata=request.metadata,
        )

        return VectorSyncResponse(
            success=success,
            entity_id=str(resume_id),
            entity_type="resume",
            message="Sync completed successfully" if success else "Sync failed",
            chroma_synced=success,
        )
    except Exception as e:
        logger.error(f"Resume sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.post("/sync/job/{job_id}", response_model=VectorSyncResponse)
async def sync_job_vectors(
    job_id: UUID, request: VectorSyncRequest, db: AsyncSession = Depends(get_db)
):
    try:
        success = await vector_sync_service.sync_job(
            db=db,
            job_id=str(job_id),
            job_text=request.content,
            metadata=request.metadata,
        )

        return VectorSyncResponse(
            success=success,
            entity_id=str(job_id),
            entity_type="job",
            message="Sync completed" if success else "Sync failed",
            chroma_synced=success,
        )
    except Exception as e:
        logger.error(f"Job sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.post("/sync/batch/resumes")
async def batch_sync_resumes(
    resumes: List[Dict],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        background_tasks.add_task(vector_sync_service.batch_sync_resumes, db, resumes)

        return {
            "message": f"Batch sync started for {len(resumes)} resumes",
            "status": "processing",
        }
    except Exception as e:
        logger.error(f"Batch sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Monitoring
@router.get(
    "/consistency/{entity_type}/{entity_id}", response_model=ConsistencyCheckResponse
)
async def check_vector_consistency(
    entity_type: str, entity_id: UUID, db: AsyncSession = Depends(get_db)
):

    try:
        result = await vector_sync_service.verify_consistency(
            db=db, entity_id=str(entity_id), entity_type=entity_type
        )

        return ConsistencyCheckResponse(**result)
    except Exception as e:
        logger.error(f"Consistency check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# @router.get("/audit")
# async def get_sync_audit_logs(
#     entity_type: Optional[str] = None,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db),
# ):

#     try:
#         logs = await vector_sync_service.get_sync_audit_report(
#             db=db, entity_type=entity_type, limit=limit
#         )
#         return {"total": len(logs), "logs": logs}
#     except Exception as e:
#         logger.error(f"Audit log retrieval failed: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         )


@router.get("/stats")
async def get_vector_db_stats(db: AsyncSession = Depends(get_db)):

    try:
        from app.utils.chroma_manager import chroma_manager

        # Get Chroma stats
        chroma_resume_stats = chroma_manager.get_collection_stats("resume_embeddings")
        chroma_job_stats = chroma_manager.get_collection_stats("job_embeddings")

        return {
            "database": "chromadb",
            "collections": {"resumes": chroma_resume_stats, "jobs": chroma_job_stats},
            "total_documents": (
                chroma_resume_stats.get("document_count", 0)
                + chroma_job_stats.get("document_count", 0)
            ),
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
