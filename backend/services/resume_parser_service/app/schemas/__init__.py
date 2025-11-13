"""Resume-related Pydantic schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    """Base resume schema."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, etc.)")


class ResumeCreate(ResumeBase):
    """Schema for creating a resume."""

    user_id: UUID
    file_path: str
    file_size: int


class ResumeUpdate(BaseModel):
    """Schema for updating a resume."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    """Response after uploading a resume."""

    resume_id: UUID
    filename: str
    file_size: int
    message: str
    status: str


class ResumeParseResponse(BaseModel):
    """Response after parsing a resume."""

    resume_id: UUID
    message: str
    status: str
    parsed_data: Optional[dict] = None
    error: Optional[str] = None


class ResumeParsed(BaseModel):
    """Schema for parsed resume data."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[dict] = None
    experience: Optional[list] = None
    education: Optional[list] = None
    certifications: Optional[list] = None
    languages: Optional[list] = None
    total_experience_years: Optional[float] = None
    summary: Optional[str] = None


class ResumeEmbedding(BaseModel):
    """Schema for resume embedding."""

    resume_id: UUID
    embedding: List[float]
    model_name: str
    dimension: int


class ResumeRead(BaseModel):
    """Schema for reading a single resume."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    file_type: str

    # Extracted data
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

    # ✅ FIXED: Changed from dict to list
    skills: Optional[dict] = None
    experience: Optional[list] = None  # List of experience dicts
    education: Optional[list] = None  # List of education dicts
    certifications: Optional[list] = None  # List of certifications
    languages: Optional[list] = None  # List of languages

    total_experience_years: Optional[float] = None

    # Embedding info
    embedding_model: Optional[str] = None
    is_embedding_generated: bool = False

    # Parsing status
    is_parsed: bool = False
    parsing_error: Optional[str] = None
    parsing_version: Optional[str] = None
    last_parsed_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False


class ResumeResponse(BaseModel):
    """Schema for resume response (same as ResumeRead for compatibility)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    file_type: str

    # Extracted data
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

    # ✅ FIXED: Changed from dict to list
    skills: Optional[dict] = None
    experience: Optional[list] = None  # List of experience dicts
    education: Optional[list] = None  # List of education dicts
    certifications: Optional[list] = None  # List of certifications
    languages: Optional[list] = None  # List of languages

    total_experience_years: Optional[float] = None

    # Embedding info
    embedding_model: Optional[str] = None
    is_embedding_generated: bool = False

    # Parsing status
    is_parsed: bool = False
    parsing_error: Optional[str] = None
    parsing_version: Optional[str] = None
    last_parsed_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False


class ResumeList(BaseModel):
    """Schema for list of resumes."""

    resumes: List[ResumeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResumeStats(BaseModel):
    """Schema for resume statistics."""

    total_resumes: int
    parsed_resumes: int
    with_embeddings: int
    parsing_rate: float
    embedding_rate: float


class ResumePreview(BaseModel):
    """Schema for resume text preview."""

    resume_id: UUID
    filename: str
    total_lines: int
    preview_lines: List[str]
    has_more: bool
