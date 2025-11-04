"""Pytest configuration and fixtures."""

# Step 1: Setup Python path FIRST (before ANY imports)
import sys
from pathlib import Path

shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Step 2: Standard library imports
import os
import uuid
from datetime import datetime

# Step 3: Third-party imports
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

# Step 4: Local imports (now safe because PYTHONPATH is set)
from app.db.base import Base
from app.models.application import Application, ApplicationStatus
from app.models.category import Category
from app.models.job import ExperienceLevel, Job, JobStatus, JobType
from app.models.skill import Skill
from app.services.job_service import JobService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create test database engine with all tables"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables from Base metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as s:
        yield s


@pytest.fixture
def job_service(session):
    """Create job service instance with test session"""
    return JobService(session)


@pytest.fixture
def sample_job():
    """Sample job data for testing"""
    return {
        "title": "Senior Python Developer",
        "description": "Looking for an experienced Python developer",
        "job_type": "FULL_TIME",
        "experience_level": "SENIOR",
        "salary_min": 100000,
        "salary_max": 150000,
        "location": "San Francisco, CA",
        "is_remote": True,
    }
