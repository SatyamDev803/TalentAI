from typing import Dict, Any
import json
import google.generativeai as genai
from enum import Enum

from app.core.cache import cache_service

from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RecommendationType(str, Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    CONSIDER = "CONSIDER"
    NO_HIRE = "NO_HIRE"


class RecommendationChain:

    def __init__(self):

        api_key = settings.google_api_key
        if not api_key:
            logger.warning("GOOGLE_API_KEY not configured")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    async def recommend(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        match_scores: Dict[str, float],
        skill_gap_analysis: Dict[str, Any],
        job_id: str = "unknown",
        candidate_id: str = "unknown",
        skip_cache: bool = False,
    ) -> Dict[str, Any]:

        if not skip_cache:
            cached_result = await cache_service.get_llm_recommendation(
                job_id, candidate_id
            )
            if cached_result:
                logger.info(
                    f"Recommendation cache HIT for {job_id}-{candidate_id} (saved ~4s)"
                )
                return cached_result

        logger.info(
            f"Recommendation cache MISS for {job_id}-{candidate_id} - Generating..."
        )

        try:
            prompt = f"""You are a senior recruiter making hiring decisions.

Job Requirements:
Title: {job_data.get("title", "")}
Required Skills: {", ".join(job_data.get("required_skills", []))}
Seniority: {job_data.get("seniority", "Mid-level")}

Candidate Assessment:
Skills: {", ".join(candidate_data.get("skills", []))}
Experience: {candidate_data.get("years_experience", 0)} years
Overall Match Score: {round(match_scores.get("overall_score", 0) * 100, 1)}%

Skill Gap Analysis:
Matching Skills: {", ".join(skill_gap_analysis.get("matching_skills", []))}
Missing Skills: {", ".join(skill_gap_analysis.get("missing_skills", []))}
Skill Gap: {skill_gap_analysis.get("skill_gap_percentage", 50)}%

Provide hiring recommendation based on this information.

Guidelines:
- STRONG_HIRE: 85%+ match, minimal gaps, ready to excel
- HIRE: 70-84% match, minor gaps, can grow into role
- CONSIDER: 55-69% match, significant gaps, risky but possible
- NO_HIRE: <55% match, too many gaps, not recommended

Respond ONLY with valid JSON:
{{
  "recommendation": "STRONG_HIRE/HIRE/CONSIDER/NO_HIRE",
  "confidence_score": 75.0,
  "reasoning": "Detailed reasoning for this recommendation",
  "next_steps": "Suggested next steps in hiring process",
  "interview_focus_areas": "Key areas to focus on during interview"
}}"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                ),
            )

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())

            # Cache the result
            await cache_service.cache_llm_recommendation(job_id, candidate_id, result)

            logger.info(
                f"Recommendation generated and cached: {result.get('recommendation')}"
            )
            return result

        except Exception as e:
            logger.error(f"ecommendation failed: {e}")
            return {
                "recommendation": "CONSIDER",
                "confidence_score": 50.0,
                "reasoning": f"Error: {str(e)}",
                "next_steps": "Manual review required",
                "interview_focus_areas": "All areas",
            }


recommendation_chain = RecommendationChain()
