from common.exceptions import ResourceNotFoundError, ValidationError
from common.logger import logger
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import (get_current_active_user, get_job_service,
                           require_role)
from app.schemas.application import (ApplicationCreate,
                                     ApplicationListResponse, ApplicationRead)
from app.schemas.job import JobCreate, JobListResponse, JobRead, JobUpdate
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Create a new job"""
    try:
        company_id = current_user.get("company_id")
        user_id = current_user.get("id")

        if not company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be part of a company to create jobs",
            )

        job = await job_service.create_job(
            job_data, company_id=company_id, user_id=user_id
        )
        return job
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
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
    current_user: dict = Depends(get_current_active_user),
    job_service: JobService = Depends(get_job_service),
) -> JobListResponse:
    """List published jobs with filters"""
    try:
        filters = {
            "query": query,
            "experience_level": experience_level,
            "location": location,
            "is_remote": is_remote,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "job_type": job_type,
        }
        jobs, total = await job_service.list_jobs(page, page_size, query, filters)
        return JobListResponse(total=total, jobs=jobs)
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs",
        )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_active_user),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Get job details"""
    try:
        job = await job_service.get_job_by_id(job_id)
        return job
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job",
        )


@router.put("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Update job"""
    try:
        job = await job_service.update_job(job_id, job_data)
        return job
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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
    job_id: str,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> None:
    """Delete job"""
    try:
        await job_service.delete_job(job_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job",
        )


@router.post("/{job_id}/publish", response_model=JobRead)
async def publish_job(
    job_id: str,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Publish job"""
    try:
        job = await job_service.publish_job(job_id)
        return job
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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
    job_id: str,
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Close job"""
    try:
        job = await job_service.close_job(job_id)
        return job
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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
    job_id: str,
    application_data: ApplicationCreate,
    current_user: dict = Depends(require_role("CANDIDATE")),
    job_service: JobService = Depends(get_job_service),
) -> ApplicationRead:
    """Apply for job"""
    try:
        application = await job_service.apply_for_job(
            job_id=job_id,
            candidate_id=current_user.get("id"),
            app_data=application_data,
        )
        return application
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying for job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to apply"
        )


@router.get("/{job_id}/applications", response_model=ApplicationListResponse)
async def get_job_applications(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("RECRUITER")),
    job_service: JobService = Depends(get_job_service),
) -> ApplicationListResponse:
    """Get job applications"""
    try:
        applications, total = await job_service.get_job_applications(
            job_id, page, page_size
        )
        return ApplicationListResponse(total=total, applications=applications)
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications",
        )
