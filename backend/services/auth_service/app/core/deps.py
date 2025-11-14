from typing import Optional
from uuid import UUID

from common.logging import get_logger
from common.redis_client import redis_client
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

logger = get_logger(__name__)

# Bearer token
security = HTTPBearer(auto_error=False)


async def get_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None, alias="access_token"),
) -> str:
    # Try Bearer token first
    if credentials:
        logger.debug("Token from Bearer header")
        return credentials.credentials

    # Fallback to cookie
    if access_token:
        logger.debug("Token from cookie")
        return access_token

    # No token found
    logger.warning("Authentication attempt without token")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide token via Bearer header or cookie.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)

    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    jti: str = payload.get("jti")

    if not user_id or token_type != "access":
        logger.warning(f"Invalid token claims: user_id={user_id}, type={token_type}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token blacklist
    is_blacklisted = await redis_client.is_token_blacklisted(jti)
    if is_blacklisted:
        logger.warning(f"Blacklisted token used: jti={jti}, user={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user ID format
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Invalid user ID format: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        logger.warning(f"Token references non-existent user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"User authenticated: {user_id}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


async def get_current_user_for_refresh(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)

    if not payload:
        logger.warning("Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    jti: str = payload.get("jti")

    if not user_id or token_type != "refresh":
        logger.warning(
            f"Invalid refresh token claims: user_id={user_id}, type={token_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify refresh token is still in Redis
    stored_user_id = await redis_client.get_refresh_token_user(jti)
    if not stored_user_id or stored_user_id != user_id:
        logger.warning(f"Refresh token revoked or invalid: jti={jti}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user ID format
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Invalid user ID in refresh token: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        logger.warning(f"Refresh token references non-existent user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"User refreshed token: {user_id}")
    return user


# Role-Based Access Control


def require_role(*roles: UserRole):
    async def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            logger.warning(
                f"Role check failed: user={current_user.id}, "
                f"has={current_user.role}, required={roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized. Required roles: {roles}",
            )
        return current_user

    return check_role


async def require_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_verified:
        logger.warning(f"Unverified user attempted protected action: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address must be verified to perform this action",
        )
    return current_user


async def require_company_member(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.company_id:
        logger.warning(f"Non-company user attempted company action: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company to perform this action",
        )
    return current_user


async def require_company_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.RECRUITER):
        logger.warning(
            f"Non-admin attempted admin action: user={current_user.id}, role={current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and admins allowed",
        )

    if not current_user.company_id:
        logger.warning(f"Admin without company attempted action: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company",
        )

    return current_user
