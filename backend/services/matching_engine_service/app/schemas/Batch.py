from typing import List, Optional
from pydantic import BaseModel, Field


class BatchMatchRequest(BaseModel):

    job_id: str = Field(..., description="Job ID to match against")
    candidate_ids: List[str] = Field(
        ...,
        description="List of candidate IDs (1-100 candidates)",
        min_length=1,
        max_length=100,
    )
    use_vector_search: bool = Field(
        default=False, description="Enable vector similarity scoring"
    )
    min_score_threshold: Optional[float] = Field(
        default=None, description="Minimum score threshold (0-100)", ge=0, le=100
    )
    store_results: bool = Field(
        default=False, description="Store top 10 results in database"
    )


class CandidateMatchResult(BaseModel):

    candidate_id: str
    rank: int
    overall_score: float
    breakdown: dict
    vector_similarity: Optional[float] = None
    processing_time_ms: float
    computed_at: str


class BatchMatchResponse(BaseModel):

    status: str
    job_id: str
    total_candidates: int
    matched_candidates: int
    results: List[CandidateMatchResult]
    processing_time_seconds: float
    metadata: dict
