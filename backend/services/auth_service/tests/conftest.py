import sys
from pathlib import Path

shared_path = Path(__file__).parent.parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    # Create event loop for async tests
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
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
    return {
        "email": "test@example.com",
        "password": "SecurePassword123",
        "full_name": "Test User",
        "role": "CANDIDATE",
    }


@pytest_asyncio.fixture
async def client(test_db, monkeypatch):

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user_data():
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123",
        "full_name": "Admin User",
        "role": UserRole.ADMIN.value,
    }


@pytest.fixture
def recruiter_user_data():
    return {
        "email": "recruiter@example.com",
        "password": "RecruiterPassword123",
        "full_name": "Recruiter User",
        "role": UserRole.RECRUITER.value,
    }
