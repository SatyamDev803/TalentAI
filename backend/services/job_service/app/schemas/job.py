"""Job schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class JobCreate(BaseModel):
    """Create job request."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    job_type: Optional[str] = Field(None, max_length=50)
    experience_level: Optional[str] = Field(None, max_length=50)
    category_id: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = False


class JobUpdate(BaseModel):
    """Update job request."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    job_type: Optional[str] = Field(None, max_length=50)
    experience_level: Optional[str] = Field(None, max_length=50)
    category_id: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = False


class JobRead(BaseModel):
    """Job response."""

    id: str = Field(...)
    title: str
    description: str
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    company_id: str = Field(...)
    created_by_id: str = Field(...)
    category_id: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    is_remote: bool = False
    status: str = "DRAFT"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_validator("id", "company_id", "created_by_id", "category_id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class JobListResponse(BaseModel):
    """List jobs response."""

    total: int
    jobs: list[JobRead]
