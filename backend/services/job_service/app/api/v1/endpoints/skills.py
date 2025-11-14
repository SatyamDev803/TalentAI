from common.exceptions import ResourceNotFoundError, ValidationError
from common.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_active_user, get_skill_service, require_role
from app.schemas.skill import SkillCreate, SkillListResponse, SkillRead
from app.services.skill_service import SkillService

logger = get_logger(__name__)

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=SkillListResponse, status_code=status.HTTP_200_OK)
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    skill_service: SkillService = Depends(get_skill_service),
) -> SkillListResponse:

    try:
        skills, total = await skill_service.list_skills(page, page_size)
        return SkillListResponse(
            total=total,
            skills=skills,
        )
    except Exception as e:
        logger.error(f"Error listing skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list skills",
        )


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: dict = Depends(require_role("ADMIN")),
    skill_service: SkillService = Depends(get_skill_service),
) -> SkillRead:

    try:
        skill = await skill_service.create_skill(skill_data)
        return skill
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create skill",
        )


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user: dict = Depends(require_role("ADMIN")),
    skill_service: SkillService = Depends(get_skill_service),
) -> None:

    try:
        await skill_service.delete_skill(skill_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete skill",
        )
