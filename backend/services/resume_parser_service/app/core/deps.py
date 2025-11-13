"""Dependencies for dependency injection."""

from typing import Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache, get_cache
from app.core.security import decode_access_token
from app.db.session import get_db
from app.services.resume_service import ResumeService

# HTTP Bearer for JWT token (optional)
security = HTTPBearer(auto_error=False)


async def get_cache_client() -> RedisCache:
    """Get Redis cache client."""
    return await get_cache()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
) -> dict:
    """Get current user from JWT token (Bearer or Cookie).

    Args:
        credentials: HTTP Bearer credentials (optional)
        access_token: JWT token from cookie (optional)

    Returns:
        User data from token

    Raises:
        HTTPException: If token is invalid
    """
    # Try Bearer token first, then cookie
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Active user data

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return current_user


async def get_resume_service(
    db: AsyncSession = Depends(get_db),
) -> ResumeService:
    """Get resume service instance.

    Args:
        db: Database session

    Returns:
        Resume service instance
    """
    return ResumeService(db)


def get_user_id(current_user: dict = Depends(get_current_active_user)) -> UUID:
    """Extract user ID from current user."""
    # Try multiple possible user ID fields
    user_id = (
        current_user.get("user_id") or current_user.get("sub") or current_user.get("id")
    )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    try:
        return UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID format: {user_id}",
        )
