"""Pytest configuration and fixtures."""

# Step 1: Setup path FIRST
import sys
from pathlib import Path

shared_path = Path(__file__).parent.parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Step 2: Standard library
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

# Step 3: Third-party
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Step 4: Local (now safe!)
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123",
        "full_name": "Test User",
        "role": "CANDIDATE",
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "name": "Test Company",
        "industry": "Technology",
        "size": "medium",
        "subscription_tier": "pro",
    }


@pytest_asyncio.fixture
async def client(test_db, monkeypatch):
    """Create test client."""

    # Mock get_db to return test_db
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
