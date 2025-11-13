"""Test configuration and fixtures."""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.main import app
from app.core.deps import get_db, get_current_active_user, get_user_id

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://talentai_dev:dev_password_123@localhost:5432/talentai_resume_test",
)


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest."""
    config.option.asyncio_mode = "auto"


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create engine for THIS test only
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=None,  # Disable pooling
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture
def test_user_id() -> uuid.UUID:
    """Test user ID."""
    return uuid.UUID("4bb8a7d6-b47b-4ca7-ba9c-4efc08df4b8b")


@pytest.fixture
def mock_user(test_user_id) -> dict:
    """Mock authenticated user."""
    return {
        "sub": str(test_user_id),
        "email": "test@example.com",
        "role": "CANDIDATE",
        "company_id": None,
    }


@pytest.fixture
def auth_headers() -> dict:
    """Authentication headers (not used when auth is bypassed)."""
    return {}


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, mock_user: dict, test_user_id: uuid.UUID
) -> AsyncGenerator[AsyncClient, None]:
    """Test client with database override and auth bypass."""

    # Override database dependency
    async def override_get_db():
        yield db_session

    # Override auth dependencies (bypass JWT verification)
    async def override_get_current_active_user():
        return mock_user

    async def override_get_user_id():
        return test_user_id

    # Apply overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_user_id] = override_get_user_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing."""
    return """
    John Doe
    john.doe@example.com
    (555) 123-4567
    
    EXPERIENCE:
    Senior Software Engineer at Google (2020-Present)
    - Developed microservices using Python and FastAPI
    - Built frontend applications with React and TypeScript
    
    SKILLS:
    Python, JavaScript, TypeScript, FastAPI, React, Docker, AWS
    
    EDUCATION:
    B.S. in Computer Science
    MIT, 2018
    """


@pytest.fixture
def test_resume_file(tmp_path) -> Path:
    """Create a test PDF file."""
    file_path = tmp_path / "test_resume.pdf"
    # Create dummy PDF content
    file_path.write_bytes(b"%PDF-1.4\nTest Resume Content")
    return file_path


@pytest.fixture
def sample_resume_data(test_user_id):
    """Sample resume creation data."""
    from app.schemas.resume import ResumeCreate

    return ResumeCreate(
        user_id=test_user_id,
        filename="test_resume.pdf",
        file_path="/uploads/test_resume.pdf",
        file_size=12345,
        file_type="pdf",
    )


# Async event loop fixture for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy."""
    return asyncio.get_event_loop_policy()
