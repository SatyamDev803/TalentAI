from common.redis_client import redis_client
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import JobServiceConfig
from app.core.security import decode_token
from app.db.session import get_db
from app.services.application_service import ApplicationService
from app.services.category_service import CategoryService
from app.services.job_service import JobService
from app.services.skill_service import SkillService

settings = JobServiceConfig()


async def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return token


async def get_current_user(
    token: str = Depends(get_token_from_cookie),
) -> dict:
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    token_type = payload.get("type")
    jti = payload.get("jti")

    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )

    # Check blacklist
    is_blacklisted = await redis_client.is_token_blacklisted(jti)
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
        )

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
    # Require specific roles

    async def check_role(current_user: dict = Depends(get_current_active_user)) -> dict:
        # Check if user has required role
        user_role = current_user.get("role")
        if user_role not in roles:
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be part of a company to perform this action",
        )
    return current_user


async def require_company_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
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


# Job Service Dependencies


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
