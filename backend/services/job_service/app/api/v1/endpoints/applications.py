from common.exceptions import ResourceNotFoundError, ValidationError
from common.logger import logger
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import (get_application_service, get_current_active_user,
                           require_role)
from app.schemas.application import (ApplicationCreate,
                                     ApplicationListResponse, ApplicationRead,
                                     ApplicationUpdate)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_job(
    job_id: str,
    application_data: ApplicationCreate,
    current_user: dict = Depends(require_role("CANDIDATE")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:
    """Apply for a job (Candidate only)"""
    try:
        application = await app_service.apply_for_job(
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


@router.get("", response_model=ApplicationListResponse, status_code=status.HTTP_200_OK)
async def list_my_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("CANDIDATE")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationListResponse:
    """List my applications (Candidate only)"""
    try:
        applications, total = await app_service.get_candidate_applications(
            candidate_id=current_user.get("id"),
            page=page,
            page_size=page_size,
        )
        return ApplicationListResponse(total=total, applications=applications)
    except Exception as e:
        logger.error(f"Error listing applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications",
        )


@router.get(
    "/{application_id}", response_model=ApplicationRead, status_code=status.HTTP_200_OK
)
async def get_application(
    application_id: str,
    current_user: dict = Depends(get_current_active_user),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:
    """Get application details"""
    try:
        application = await app_service.get_application_by_id(application_id)
        return application
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get application",
        )


@router.put(
    "/{application_id}", response_model=ApplicationRead, status_code=status.HTTP_200_OK
)
async def update_application_status(
    application_id: str,
    status_update: ApplicationUpdate,
    current_user: dict = Depends(require_role("RECRUITER")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:
    """Update application status (Recruiter only)"""
    try:
        application = await app_service.update_application_status(
            application_id=application_id,
            status_data=status_update,
        )
        return application
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application",
        )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    application_id: str,
    current_user: dict = Depends(require_role("CANDIDATE")),
    app_service: ApplicationService = Depends(get_application_service),
) -> None:
    """Withdraw application (Candidate only)"""
    try:
        await app_service.withdraw_application(application_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error withdrawing application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to withdraw",
        )


@router.get(
    "/jobs/{job_id}/applications",
    response_model=ApplicationListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_job_applications(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("RECRUITER")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationListResponse:
    """Get all applications for a job (Recruiter only)"""
    try:
        applications, total = await app_service.get_job_applications(
            job_id=job_id,
            page=page,
            page_size=page_size,
        )
        return ApplicationListResponse(total=total, applications=applications)
    except Exception as e:
        logger.error(f"Error listing job applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications",
        )
