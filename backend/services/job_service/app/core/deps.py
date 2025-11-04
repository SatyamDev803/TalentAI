"""Dependency injection for FastAPI endpoints - Job Service."""

from typing import Optional

from common.logger import logger
from common.redis_client import redis_client
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import JobServiceConfig
from app.core.security import decode_token
from app.db.session import get_db
from app.services.application_service import ApplicationService
from app.services.category_service import CategoryService
from app.services.job_service import JobService
from app.services.skill_service import SkillService

settings = JobServiceConfig()


async def get_token_from_header(
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


async def get_current_user(
    token: str = Depends(get_token_from_header),
) -> dict:
    """Get current user from JWT token (NO DATABASE QUERY)."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

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

    # Extract role and convert from "UserRole.ADMIN" to "ADMIN"
    role = payload.get("role", "CANDIDATE")
    if isinstance(role, str) and role.startswith("UserRole."):
        role = role.replace("UserRole.", "")

    # Extract company_id - IMPORTANT!
    company_id = payload.get("company_id")  # ← FIX: Was missing!
    logger.info(f"Token payload - company_id: {company_id}, role: {role}")

    # Return user info from token (no DB query)
    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": role,
        "company_id": company_id,  # ← FIX: Add this!
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active user."""
    return current_user


def require_role(*roles: str):
    """Require specific roles."""

    async def check_role(current_user: dict = Depends(get_current_active_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' not authorized. Required: {roles}",
            )
        return current_user

    return check_role


async def require_verified_user(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """Require verified user (trust token)."""
    return current_user


async def require_company_member(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """Require company member."""
    if not current_user.get("company_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company",
        )
    return current_user


async def require_company_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """Require company admin/recruiter."""
    user_role = current_user.get("role")
    if user_role not in ("ADMIN", "RECRUITER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and admins allowed",
        )

    if not current_user.get("company_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company",
        )

    return current_user


# ==================== Job Service Dependencies ====================


async def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


async def get_application_service(
    db: AsyncSession = Depends(get_db),
) -> ApplicationService:
    return ApplicationService(db)


async def get_skill_service(db: AsyncSession = Depends(get_db)) -> SkillService:
    return SkillService(db)


async def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(db)
