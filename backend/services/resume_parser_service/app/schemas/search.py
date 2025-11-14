from typing import List
from pydantic import BaseModel, Field

from app.schemas.resume import ResumeRead


class SearchMetadata(BaseModel):

    total_results: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="Original search query")
    search_time_seconds: float = Field(..., description="Time taken to execute search")
    min_score_threshold: float = Field(..., description="Minimum similarity threshold")
    top_k: int = Field(..., description="Maximum results to return")


class MatchReason(BaseModel):

    category: str = Field(
        ..., description="Category of match (skills, experience, etc)"
    )
    details: str = Field(..., description="Specific details about the match")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")


class ResumeSearchResult(BaseModel):

    resume: ResumeRead = Field(..., description="Resume details")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Cosine similarity score"
    )
    match_percentage: int = Field(
        ..., ge=0, le=100, description="Match percentage (0-100)"
    )
    match_reasons: List[str] = Field(
        default_factory=list, description="Why this resume matched"
    )
    rank: int = Field(..., ge=1, description="Rank in search results")


class EnhancedSearchResponse(BaseModel):

    results: List[ResumeSearchResult] = Field(
        default_factory=list, description="Search results"
    )
    metadata: SearchMetadata = Field(..., description="Search metadata")


class ExportFormat(str):
    """Export format options."""

    CSV = "csv"
    JSON = "json"
