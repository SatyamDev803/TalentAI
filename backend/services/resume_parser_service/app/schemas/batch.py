"""Batch upload schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class BatchUploadResult(BaseModel):
    """Result for a single file in batch upload."""

    filename: str = Field(..., description="Original filename")
    resume_id: Optional[uuid.UUID] = Field(None, description="Created resume ID")
    status: str = Field(..., description="Status: uploaded, failed, skipped")
    error: Optional[str] = Field(None, description="Error message if failed")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    queued_for_parsing: bool = Field(
        default=False, description="Whether queued for async parsing"
    )


class BatchUploadResponse(BaseModel):
    """Response for batch upload operation."""

    total_files: int = Field(..., description="Total files received")
    uploaded: int = Field(..., description="Successfully uploaded count")
    failed: int = Field(..., description="Failed upload count")
    skipped: int = Field(..., description="Skipped file count")
    results: List[BatchUploadResult] = Field(
        default_factory=list, description="Per-file results"
    )
    processing_time_seconds: float = Field(..., description="Total processing time")
