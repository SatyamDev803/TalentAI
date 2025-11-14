from typing import Optional
from uuid import UUID

from common.logging import get_logger
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache, get_cache
from app.core.security import decode_access_token
from app.db.session import get_db
from app.services.resume_service import ResumeService

logger = get_logger(__name__)

# Bearer token
security = HTTPBearer(auto_error=False)


async def get_cache_client() -> RedisCache:
    return await get_cache()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None, alias="access_token"),
) -> dict:
    # Try Bearer token first
    token = None
    if credentials:
        logger.debug("Token from Bearer header")
        token = credentials.credentials
    elif access_token:
        logger.debug("Token from cookie")
        token = access_token

    if not token:
        logger.warning("Authentication attempt without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide token via Bearer header or cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)

        if payload is None:
            logger.warning("Token decode failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(f"User authenticated: {payload.get('sub')}")
        return payload

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not current_user.get("is_active", True):
        logger.warning(f"Inactive user attempted access: {current_user.get('sub')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_resume_service(
    db: AsyncSession = Depends(get_db),
) -> ResumeService:
    return ResumeService(db)


def get_user_id(current_user: dict = Depends(get_current_active_user)) -> UUID:
    # Try multiple possible user ID fields
    user_id = (
        current_user.get("user_id") or current_user.get("sub") or current_user.get("id")
    )

    if not user_id:
        logger.error(f"User ID not found in token: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    try:
        return UUID(user_id)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid user ID format: {user_id}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID format: {user_id}",
        )
