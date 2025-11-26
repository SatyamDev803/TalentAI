from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import hashlib

from app.chains import chain_orchestrator
from app.chains.skill_gap_chain import skill_gap_chain
from app.chains.explanation_chain import explanation_chain
from app.chains.recommendation_chain import recommendation_chain
from app.schemas.AnalysisRequest import AnalysisRequest
from common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _extract_or_generate_id(data: Dict[str, Any], prefix: str) -> str:
    # Try to get existing ID
    for key in ["id", "job_id", "candidate_id", "_id"]:
        if key in data and data[key]:
            return str(data[key])

    # Generate deterministic ID from data
    data_str = str(sorted(data.items()))
    hash_obj = hashlib.md5(data_str.encode())
    return f"{prefix}_{hash_obj.hexdigest()[:8]}"


@router.post("/analyze/skill-gap")
async def analyze_skill_gap(request: AnalysisRequest):

    try:
        # Extract or generate IDs for caching
        job_id = _extract_or_generate_id(request.job_data, "job")
        candidate_id = _extract_or_generate_id(request.candidate_data, "cand")

        logger.info(f"Skill gap analysis: job={job_id}, candidate={candidate_id}")

        result = await skill_gap_chain.analyze(
            request.job_data,
            request.candidate_data,
            job_id=job_id,
            candidate_id=candidate_id,
        )
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.error(f"Skill gap analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/explanation")
async def generate_explanation(request: AnalysisRequest):

    try:
        if not request.match_scores:
            request.match_scores = {
                "overall_score": 0.75,
                "skill_score": 0.80,
                "experience_score": 0.70,
            }

        job_id = _extract_or_generate_id(request.job_data, "job")
        candidate_id = _extract_or_generate_id(request.candidate_data, "cand")

        logger.info(f"Explanation generation: job={job_id}, candidate={candidate_id}")

        result = await explanation_chain.explain(
            request.job_data,
            request.candidate_data,
            request.match_scores,
            job_id=job_id,
            candidate_id=candidate_id,
        )
        return {"status": "success", "explanation": result}
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/recommendation")
async def generate_recommendation(request: AnalysisRequest):

    try:
        if not request.match_scores:
            request.match_scores = {
                "overall_score": 0.75,
                "skill_score": 0.80,
                "experience_score": 0.70,
            }

        job_id = _extract_or_generate_id(request.job_data, "job")
        candidate_id = _extract_or_generate_id(request.candidate_data, "cand")

        logger.info(
            f"Recommendation generation: job={job_id}, candidate={candidate_id}"
        )

        # First get skill gap analysis
        skill_gap = await skill_gap_chain.analyze(
            request.job_data,
            request.candidate_data,
            job_id=job_id,
            candidate_id=candidate_id,
        )

        # Then generate recommendation
        result = await recommendation_chain.recommend(
            request.job_data,
            request.candidate_data,
            request.match_scores,
            skill_gap,
            job_id=job_id,
            candidate_id=candidate_id,
        )
        return {
            "status": "success",
            "recommendation": result,
            "skill_gap_context": skill_gap,
        }
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/full")
async def full_analysis(request: AnalysisRequest):

    try:
        if not request.match_scores:
            request.match_scores = {
                "overall_score": 0.75,
                "skill_score": 0.80,
                "experience_score": 0.70,
            }

        job_id = _extract_or_generate_id(request.job_data, "job")
        candidate_id = _extract_or_generate_id(request.candidate_data, "cand")

        logger.info(f"Full analysis: job={job_id}, candidate={candidate_id}")

        result = await chain_orchestrator.full_analysis(
            request.job_data,
            request.candidate_data,
            request.match_scores,
            job_id=job_id,
            candidate_id=candidate_id,
        )
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.error(f"Full analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
