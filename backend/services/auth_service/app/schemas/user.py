from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.CANDIDATE


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    company_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_id: Optional[UUID] = None
    role: Optional[UserRole] = None


class UserRead(UserBase):
    id: UUID
    company_id: Optional[UUID]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123",
            }
        }
    )
