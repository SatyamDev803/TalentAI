"""Application schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ApplicationCreate(BaseModel):
    """Create application request."""

    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationUpdate(BaseModel):
    """Update application request."""

    status: Optional[str] = None
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationRead(BaseModel):
    """Application response."""

    id: str = Field(...)
    job_id: str = Field(...)
    candidate_id: str = Field(...)
    status: str = "PENDING"
    cover_letter: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_validator("id", "job_id", "candidate_id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class ApplicationListResponse(BaseModel):
    """List applications response."""

    total: int
    applications: list[ApplicationRead]
