from common.exceptions import ResourceNotFoundError, ValidationError
from common.logging import get_logger
from common.validators import validate_uuid
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import get_application_service, get_current_active_user, require_role
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationRead,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService

logger = get_logger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_job(
    job_id: str = Path(..., description="Job ID"),
    application_data: ApplicationCreate = None,
    current_user: dict = Depends(require_role("CANDIDATE")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:

    try:
        validate_uuid(job_id, "Job ID")
        application = await app_service.apply_for_job(
            job_id=job_id,
            candidate_id=current_user.get("id"),
            app_data=application_data,
        )
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


@router.get("", response_model=ApplicationListResponse, status_code=status.HTTP_200_OK)
async def list_my_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("CANDIDATE")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationListResponse:

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


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: str = Path(..., description="Application ID"),
    current_user: dict = Depends(get_current_active_user),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:

    try:
        validate_uuid(application_id, "Application ID")
        application = await app_service.get_application_by_id(application_id)
        return application
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    except Exception as e:
        logger.error(f"Error getting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get application",
        )


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application_status(
    application_id: str = Path(..., description="Application ID"),
    status_update: ApplicationUpdate = None,
    current_user: dict = Depends(get_current_active_user),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:

    try:
        validate_uuid(application_id, "Application ID")
        application = await app_service.update_application_status(
            application_id, status_update
        )
        return application
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    except Exception as e:
        logger.error(f"Error updating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application",
        )


@router.post("/{application_id}/withdraw", status_code=status.HTTP_200_OK)
async def withdraw_application(
    application_id: str = Path(..., description="Application ID"),
    current_user: dict = Depends(require_role("CANDIDATE")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationRead:

    try:
        validate_uuid(application_id, "Application ID")
        application = await app_service.withdraw_application(application_id)
        logger.info(f"Application withdrawn: {application_id}")
        return application

    except HTTPException:
        raise

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    except Exception as e:
        logger.error(f"Error withdrawing application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to withdraw application",
        )


@router.get(
    "/jobs/{job_id}/applications",
    response_model=ApplicationListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_job_applications(
    job_id: str = Path(..., description="Job ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("RECRUITER")),
    app_service: ApplicationService = Depends(get_application_service),
) -> ApplicationListResponse:

    try:
        validate_uuid(job_id, "Job ID")
        applications, total = await app_service.get_job_applications(
            job_id=job_id,
            page=page,
            page_size=page_size,
        )
        return ApplicationListResponse(total=total, applications=applications)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing job applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications",
        )
