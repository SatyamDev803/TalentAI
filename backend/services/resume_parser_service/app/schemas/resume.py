from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, etc.)")


class ResumeCreate(ResumeBase):

    user_id: UUID
    file_path: str
    file_size: int


class ResumeUpdate(BaseModel):

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None


class ResumeParsed(BaseModel):

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

    resume_id: UUID
    embedding: List[float]
    model_name: str
    dimension: int


class ResumeUploadResponse(BaseModel):

    resume_id: UUID
    filename: str
    file_size: int
    message: str
    status: str


class ResumeParseResponse(BaseModel):

    resume_id: UUID
    message: str
    status: str
    parsed_data: Optional[dict] = None
    error: Optional[str] = None


class ResumeRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    file_type: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[dict] = None
    experience: Optional[list] = None
    education: Optional[list] = None
    certifications: Optional[list] = None
    languages: Optional[list] = None
    total_experience_years: Optional[float] = None
    embedding_model: Optional[str] = None
    is_embedding_generated: bool = False
    is_parsed: bool = False
    parsing_error: Optional[str] = None
    parsing_version: Optional[str] = None
    last_parsed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False


class ResumeList(BaseModel):

    resumes: List[ResumeRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResumeStats(BaseModel):

    total_resumes: int
    parsed_resumes: int
    with_embeddings: int
    parsing_rate: float
    embedding_rate: float


class ResumePreview(BaseModel):

    resume_id: UUID
    filename: str
    total_lines: int
    preview_lines: List[str]
    has_more: bool
