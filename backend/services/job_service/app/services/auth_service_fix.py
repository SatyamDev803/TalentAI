# Add this to the end of auth_service.py to fix the dependency

from fastapi import Depends

from app.db.session import get_db


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get auth service with database session.

    Args:
        db: Database session from FastAPI dependency injection

    Returns:
        AuthService instance
    """
    return AuthService(db)
