from typing import Optional

from common.logging import get_logger
from common.redis_client import redis_client
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.services.application_service import ApplicationService
from app.services.category_service import CategoryService
from app.services.job_service import JobService
from app.services.skill_service import SkillService

logger = get_logger(__name__)

# Bearer token support
security = HTTPBearer(auto_error=False)

# Role constants
ADMIN_ROLES = {"ADMIN", "RECRUITER", "SUPER_ADMIN"}
COMPANY_ROLES = {"RECRUITER", "COMPANY_ADMIN"}


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
) -> dict:
    payload = decode_token(token)

    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    token_type = payload.get("type")
    jti = payload.get("jti")

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
            detail="Token revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"User authenticated: {user_id}")

    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role"),
        "company_id": payload.get("company_id"),
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return current_user


# Role-Based Access Control


def require_role(*roles: str):
    async def check_role(current_user: dict = Depends(get_current_active_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in roles:
            logger.warning(
                f"Role check failed: user={current_user.get('id')}, "
                f"has={user_role}, required={roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' is not authorized. Required: {roles}",
            )
        return current_user

    return check_role


async def require_verified_user(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    return current_user


async def require_company_member(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    if not current_user.get("company_id"):
        logger.warning(
            f"Non-company user attempted company action: {current_user.get('id')}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company to perform this action",
        )
    return current_user


async def require_company_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    user_role = current_user.get("role")

    if user_role not in ADMIN_ROLES:
        logger.warning(
            f"Non-admin attempted admin action: user={current_user.get('id')}, role={user_role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and admins allowed",
        )

    if not current_user.get("company_id"):
        logger.warning(
            f"Admin without company attempted action: {current_user.get('id')}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company",
        )

    return current_user


# Service Dependencies


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
