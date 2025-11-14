from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import check_db_health, get_db
from app.core.cache import get_cache, RedisCache

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "resume-parser", "version": "1.0.0"}


@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db), cache: RedisCache = Depends(get_cache)
):

    # Check database
    db_healthy = await check_db_health()

    # Check Redis
    cache_stats = await cache.get_stats()
    cache_healthy = cache_stats.get("enabled", False)

    status = "healthy" if (db_healthy and cache_healthy) else "degraded"

    return {
        "status": status,
        "service": "resume-parser",
        "version": "1.0.0",
        "dependencies": {
            "database": "healthy" if db_healthy else "unhealthy",
            "cache": "healthy" if cache_healthy else "unhealthy",
        },
        "cache_stats": cache_stats,
    }
