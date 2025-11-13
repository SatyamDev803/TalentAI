"""Database session management with async connection pooling."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.core.config import settings
from app.db.base import Base


# ═══════════════════════════════════════════════════════════
# Create async engine with connection pooling
# ═══════════════════════════════════════════════════════════

async_engine: AsyncEngine = create_async_engine(
    settings.database_url_resume,
    echo=settings.debug,
    future=True,
    # ⚡ ASYNC CONNECTION POOL SETTINGS ⚡
    # Note: For async engines, connection pooling is handled differently
    # The pool is managed by asyncpg driver internally
    pool_size=10,  # Max persistent connections
    max_overflow=20,  # Additional connections when busy
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle after 1 hour
    pool_pre_ping=True,  # Health check before use
    # For production, you can also use NullPool to disable pooling:
    # poolclass=NullPool,
)


# ═══════════════════════════════════════════════════════════
# Create async session maker
# ═══════════════════════════════════════════════════════════

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ═══════════════════════════════════════════════════════════
# Dependency for getting DB session
# ═══════════════════════════════════════════════════════════


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ═══════════════════════════════════════════════════════════
# Database health check
# ═══════════════════════════════════════════════════════════


async def check_db_health() -> bool:
    """Check if database is accessible."""
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# Startup and shutdown events
# ═══════════════════════════════════════════════════════════


async def init_db():
    """Initialize database connection."""
    print("🔗 Initializing database connection...")
    health = await check_db_health()
    if health:
        print("✅ Database connected successfully")
    else:
        print("❌ Database connection failed")

    # Create tables if they don't exist
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection and cleanup pool."""
    print("🔗 Closing database connections...")
    await async_engine.dispose()
    print("✅ Database connections closed")
