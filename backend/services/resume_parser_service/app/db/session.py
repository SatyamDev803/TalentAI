from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy import text

from app.core.config import settings
from app.db.base import Base
from common.logging import get_logger

logger = get_logger(__name__)

async_engine: AsyncEngine = create_async_engine(
    settings.database_url_resume,
    echo=settings.debug,
    future=True,
    pool_size=10,  # Max persistent connections
    max_overflow=20,  # Additional connections when busy
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle after 1 hour
    pool_pre_ping=True,  # Health check before use
    # For production, use NullPool to disable pooling
    # poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def init_db():
    logger.info("Initializing database connection...")
    health = await check_db_health()
    if health:
        logger.info("Database connected successfully")
    else:
        logger.error("Database connection failed")

    # Create tables if they don't exist
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    logger.info("Closing database connections...")
    await async_engine.dispose()
    logger.info("Database connections closed")
