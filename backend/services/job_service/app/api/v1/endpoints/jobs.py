from common.exceptions import ResourceNotFoundError, ValidationError
from common.logging import get_logger

from common.validators import validate_uuid
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from app.core.deps import get_current_active_user, get_job_service, require_role
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationRead,
)
from app.schemas.job import JobCreate, JobListResponse, JobRead, JobUpdate
from app.services.job_service import JobService
from app.core.security import decode_token

logger = get_logger(__name__)


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:

    try:
        company_id = current_user.get("company_id")
        user_id = current_user.get("id")
        if not company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be part of a company",
            )
        job = await job_service.create_job(
            job_data, company_id=company_id, user_id=user_id
        )
        logger.info(f"Job created: {job.id}")
        return job
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job",
        )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: str = Query(""),
    experience_level: str = Query(None),
    location: str = Query(None),
    is_remote: bool = Query(None),
    salary_min: int = Query(None),
    salary_max: int = Query(None),
    job_type: str = Query(None),
    request: Request = None,
    job_service: JobService = Depends(get_job_service),
) -> JobListResponse:

    try:
        token = request.cookies.get("access_token") if request else None
        current_user = None

        if token:
            payload = decode_token(token)
            if payload:
                current_user = {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role"),
                    "company_id": payload.get("company_id"),
                }

        filters = {
            "query": query,
            "experience_level": experience_level,
            "location": location,
            "is_remote": is_remote,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "job_type": job_type,
        }

        jobs, total = await job_service.list_jobs(
            page, page_size, query, filters, current_user
        )
        return JobListResponse(total=total, jobs=jobs)
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs",
        )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str = Path(..., description="Job ID"),
    current_user: dict = Depends(get_current_active_user),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:

    try:
        validate_uuid(job_id, "Job ID")
        job = await job_service.get_job_by_id(job_id)
        return job
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    except Exception as e:
        logger.error(f"Error getting job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job",
        )


@router.put("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: str = Path(...),
    job_data: JobUpdate = None,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    try:
        validate_uuid(job_id, "Job ID")
        job = await job_service.update_job(job_id, job_data)
        logger.info(f"Job updated: {job_id}")
        return job
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job",
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str = Path(...),
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> None:

    try:
        validate_uuid(job_id, "Job ID")
        await job_service.delete_job(job_id)
        logger.info(f"Job deleted: {job_id}")
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job",
        )


@router.post("/{job_id}/publish", response_model=JobRead)
async def publish_job(
    job_id: str = Path(...),
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:

    try:
        validate_uuid(job_id, "Job ID")
        job = await job_service.publish_job(job_id)
        logger.info(f"Job published: {job_id}")
        return job
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish job",
        )


@router.post("/{job_id}/close", response_model=JobRead)
async def close_job(
    job_id: str = Path(...),
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:

    try:
        validate_uuid(job_id, "Job ID")
        job = await job_service.close_job(job_id)
        logger.info(f"Job closed: {job_id}")
        return job
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close job",
        )


@router.post(
    "/{job_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_job(
    job_id: str = Path(...),
    application_data: ApplicationCreate = None,
    current_user: dict = Depends(require_role("CANDIDATE")),
    job_service: JobService = Depends(get_job_service),
) -> ApplicationRead:

    try:
        validate_uuid(job_id, "Job ID")
        application = await job_service.apply_for_job(
            job_id=job_id,
            candidate_id=current_user.get("id"),
            app_data=application_data,
        )
        logger.info(f"Application created: {application.id}")
        return application
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying for job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to apply"
        )


@router.get("/{job_id}/applications", response_model=ApplicationListResponse)
async def get_job_applications(
    job_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> ApplicationListResponse:
    try:
        validate_uuid(job_id, "Job ID")
        applications, total = await job_service.get_job_applications(
            job_id, page, page_size
        )
        return ApplicationListResponse(total=total, applications=applications)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications",
        )
