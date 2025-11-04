"""User management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    """Get current user's profile.

    **Authorization:**
    - Bearer <access_token> in Authorization header

    **Response:**
    - User profile with all details

    **Errors:**
    - 401: Invalid or expired token
    - 403: User account inactive
    """
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    """Update current user's profile.

    **Authorization:**
    - Bearer <access_token> in Authorization header

    **Request Body:**
    - full_name: (optional) New full name
    - role: (optional) New role

    **Response:**
    - Updated user profile

    **Errors:**
    - 401: Invalid token
    - 403: User inactive
    """
    try:
        updated_user = await auth_service.update_user_profile(
            current_user,
            update_data,
        )
        return updated_user
    except Exception as e:
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
    """Get user by ID (Admin/Recruiter only).

    **Authorization:**
    - Bearer <access_token> with ADMIN or RECRUITER role

    **Path Parameters:**
    - user_id: User ID to fetch

    **Response:**
    - User profile

    **Errors:**
    - 401: Invalid token
    - 403: Insufficient permissions
    - 404: User not found
    """
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("", response_model=List[UserRead])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> List[UserRead]:
    """List all users (Admin only).

    **Authorization:**
    - Bearer <access_token> with ADMIN role

    **Query Parameters:**
    - skip: Number of users to skip (default: 0)
    - limit: Maximum users to return (default: 100, max: 1000)

    **Response:**
    - List of users

    **Errors:**
    - 401: Invalid token
    - 403: Not an admin
    """
    if limit > 1000:
        limit = 1000

    users = await auth_service.list_users(skip=skip, limit=limit)
    return users


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """Deactivate a user (Admin only).

    **Authorization:**
    - Bearer <access_token> with ADMIN role

    **Path Parameters:**
    - user_id: User ID to deactivate

    **Effects:**
    - User account marked inactive
    - All tokens revoked

    **Response:**
    - 204 No Content on success

    **Errors:**
    - 401: Invalid token
    - 403: Not an admin
    - 404: User not found
    """
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        await auth_service.deactivate_user(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
