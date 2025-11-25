from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class MatchScoreBreakdown(BaseModel):
    skill: float = Field(..., ge=0, le=100)
    experience: float = Field(..., ge=0, le=100)
    location: float = Field(..., ge=0, le=100)
    salary: float = Field(..., ge=0, le=100)


class MatchScore(BaseModel):
    candidate_id: UUID
    job_id: UUID
    overall_score: float = Field(..., ge=0, le=100)
    breakdown: MatchScoreBreakdown
    quality_tier: Optional[str] = None
    confidence: Optional[float] = None
    recommendation: Optional[str] = None


class MatchExplanation(BaseModel):
    match_id: UUID
    explanation: str
    strengths: List[str]
    gaps: List[str]
    generated_at: datetime


class MatchRequest(BaseModel):
    job_id: UUID
    candidate_ids: Optional[List[UUID]] = None
    top_k: int = Field(default=10, ge=1, le=100)
    include_explanation: bool = False
    min_score: float = Field(default=0.0, ge=0, le=100)


class CandidateMatchRequest(BaseModel):
    candidate_id: UUID
    job_ids: Optional[List[UUID]] = None
    top_k: int = Field(default=10, ge=1, le=100)
    include_explanation: bool = False
    min_score: float = Field(default=0.0, ge=0, le=100)


class JobMatchRequest(BaseModel):
    job_id: UUID
    candidate_ids: Optional[List[UUID]] = None
    top_k: int = Field(default=10, ge=1, le=100)
    include_explanation: bool = False
    min_score: float = Field(default=0.0, ge=0, le=100)


class BatchMatchRequest(BaseModel):
    job_ids: List[UUID]
    candidate_ids: List[UUID]
    include_explanation: bool = False
    min_score: float = Field(default=0.0, ge=0, le=100)


class MatchResponse(BaseModel):
    match_id: UUID
    candidate_id: UUID
    job_id: UUID
    score: MatchScore
    explanation: Optional[MatchExplanation] = None
    created_at: datetime


class BatchMatchResponse(BaseModel):
    matches: List[MatchResponse]
    total_matches: int
    processing_time_ms: float
