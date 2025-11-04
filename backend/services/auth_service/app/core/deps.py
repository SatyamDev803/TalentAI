"""Dependency injection for FastAPI endpoints."""

from typing import Optional

from common.redis_client import redis_client
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AuthConfig
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

settings = AuthConfig()


async def get_token_from_header(
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract and validate token from Authorization header.

    Expected format: Bearer <token>

    Args:
        authorization: Authorization header value

    Returns:
        JWT token string

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token.

    Verifies:
    - Token signature and expiration
    - Token is not blacklisted
    - User exists and is active

    Args:
        token: JWT token from header
        db: Database session

    Returns:
        Current User object

    Raises:
        HTTPException: If token invalid or user not found
    """
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract claims
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    jti: str = payload.get("jti")

    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted
    is_blacklisted = await redis_client.is_token_blacklisted(jti)
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and verify they are active.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Current active User object

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


async def get_current_user_for_refresh(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user for token refresh (uses refresh token).

    Args:
        token: Refresh JWT token from header
        db: Database session

    Returns:
        Current User object

    Raises:
        HTTPException: If refresh token invalid or user not found
    """
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract claims
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    jti: str = payload.get("jti")

    if not user_id or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify refresh token is still in Redis (not revoked)
    stored_user_id = await redis_client.get_refresh_token_user(jti)
    if not stored_user_id or stored_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ==================== Role-Based Access Control ====================


def require_role(*roles: UserRole):
    """Dependency factory for role-based access control.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            return {"message": "Admin only"}

    Args:
        *roles: Required roles

    Returns:
        Dependency function that checks user role
    """

    async def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        """Check if user has required role.

        Args:
            current_user: Current authenticated user

        Returns:
            User if authorized

        Raises:
            HTTPException: If user lacks required role
        """
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized. Required roles: {roles}",
            )
        return current_user

    return check_role


async def require_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require user email to be verified.

    Args:
        current_user: Current authenticated user

    Returns:
        User if verified

    Raises:
        HTTPException: If user email not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address must be verified to perform this action",
        )
    return current_user


async def require_company_member(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require user to be a company member.

    Args:
        current_user: Current authenticated user

    Returns:
        User if part of a company

    Raises:
        HTTPException: If user not in a company
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company to perform this action",
        )
    return current_user


async def require_company_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require user to be a company admin/recruiter.

    Args:
        current_user: Current authenticated user

    Returns:
        User if is recruiter/admin

    Raises:
        HTTPException: If user not authorized
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.RECRUITER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and admins can perform this action",
        )

    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company",
        )

    return current_user
