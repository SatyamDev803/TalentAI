from typing import Any, Dict, Optional
from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    job_data: Dict[str, Any]
    candidate_data: Dict[str, Any]
    match_scores: Optional[Dict[str, float]] = None
