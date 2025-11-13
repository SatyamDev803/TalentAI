"""Resume database model."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Resume(Base):
    """Resume model with ML embeddings and duplicate detection."""

    __tablename__ = "resumes"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # User Information
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # File Information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )  # NEW: SHA-256 hash for duplicate detection

    # Extracted Content
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Personal Information
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Professional Summary
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_generated_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # NEW: AI-generated professional summary
    total_experience_years: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    # ML Embeddings
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(384),
        nullable=True,
    )
    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="all-MiniLM-L6-v2",
    )

    # Parsed Data (JSON)
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    experience: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    education: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    certifications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    languages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Parsing Status
    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_embedding_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    parsing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    parsing_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_parsed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Soft Delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<Resume(id={self.id}, user_id={self.user_id}, filename={self.filename})>"
        )
