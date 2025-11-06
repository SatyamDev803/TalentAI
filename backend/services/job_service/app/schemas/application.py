from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationCreate(BaseModel):
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationRead(BaseModel):
    id: str = Field(...)
    job_id: str = Field(...)
    candidate_id: str = Field(...)
    status: str = "PENDING"
    cover_letter: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "job_id", "candidate_id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class ApplicationListResponse(BaseModel):
    total: int
    applications: list[ApplicationRead]
