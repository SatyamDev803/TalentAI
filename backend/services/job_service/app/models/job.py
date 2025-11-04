import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class JobType(str, PyEnum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"


class ExperienceLevel(str, PyEnum):
    ENTRY = "ENTRY"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"


class JobStatus(str, PyEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)  # ← REMOVE ForeignKey
    created_by_id = Column(UUID(as_uuid=True), nullable=False)  # ← REMOVE ForeignKey

    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    location = Column(String(255), nullable=False)
    job_type = Column(Enum(JobType), default=JobType.FULL_TIME, nullable=False)
    experience_level = Column(
        Enum(ExperienceLevel), default=ExperienceLevel.MID, nullable=False
    )
    category_id = Column(UUID(as_uuid=True), nullable=True)  # ← REMOVE ForeignKey

    status = Column(
        Enum(JobStatus), default=JobStatus.DRAFT, nullable=False, index=True
    )
    is_remote = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Don't need relationships for microservices
    applications = relationship(
        "Application", back_populates="job", cascade="all, delete-orphan"
    )
