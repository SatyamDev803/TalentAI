"""Skill schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SkillCreate(BaseModel):
    """Create skill request."""

    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)


class SkillRead(BaseModel):
    """Skill response."""

    id: str = Field(...)
    name: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class SkillListResponse(BaseModel):
    """List skills response."""

    total: int
    skills: list[SkillRead]


class SkillUpdate(BaseModel):
    """Update skill request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
