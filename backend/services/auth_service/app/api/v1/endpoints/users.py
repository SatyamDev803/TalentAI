from typing import List

from common.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import AuthService, get_auth_service

logger = get_logger(__name__)


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:

    logger.info(f"Get current user: {current_user.id}")
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:

    try:
        logger.info(f"Updating user profile: {current_user.id}")
        updated_user = await auth_service.update_user_profile(
            current_user,
            update_data,
        )
        logger.info(f"User updated: {current_user.id}")
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:

    logger.info(f"Get user by ID: {user_id}")

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_by_id(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:

    logger.info(f"Admin updating user: {user_id}")

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        updated_user = await auth_service.update_user_profile(user, update_data)
        logger.info(f"User updated by admin: {user_id}")
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[UserRead])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> List[UserRead]:

    if limit > 1000:
        limit = 1000

    logger.info(f"Listing users: skip={skip}, limit={limit}")

    users = await auth_service.list_users(skip=skip, limit=limit)
    return users


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:

    logger.info(f"Deactivating user: {user_id}")

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        await auth_service.deactivate_user(user)
        logger.info(f"User deactivated: {user_id}")
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
