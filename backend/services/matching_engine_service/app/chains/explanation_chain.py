from typing import Dict, Any
import json
import google.generativeai as genai

from app.core.cache import cache_service
from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class ExplanationChain:

    def __init__(self):

        api_key = settings.google_api_key
        if not api_key:
            logger.warning("GOOGLE_API_KEY not configured")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    async def explain(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        match_scores: Dict[str, float],
        job_id: str = "unknown",
        candidate_id: str = "unknown",
        skip_cache: bool = False,
    ) -> Dict[str, Any]:

        if not skip_cache:
            cached_result = await cache_service.get_llm_explanation(
                job_id, candidate_id
            )
            if cached_result:
                logger.info(
                    f"Explanation cache HIT for {job_id}-{candidate_id} (saved ~5s)"
                )
                return cached_result

        logger.info(
            f"Explanation cache MISS for {job_id}-{candidate_id} - Generating..."
        )

        try:
            prompt = f"""You are an expert recruiter explaining candidate-job matches.

Job: {job_data.get("title", "")}
Required Skills: {", ".join(job_data.get("required_skills", []))}
Description: {job_data.get("description", "")[:500]}

Candidate: {candidate_data.get("name", "Candidate")}
Skills: {", ".join(candidate_data.get("skills", []))}
Experience: {candidate_data.get("years_experience", 0)} years
Summary: {candidate_data.get("summary", "")[:500]}

Match Scores:
Overall: {round(match_scores.get("overall_score", 0) * 100, 1)}%
Skill Match: {round(match_scores.get("skill_score", 0) * 100, 1)}%
Experience Match: {round(match_scores.get("experience_score", 0) * 100, 1)}%

Provide a comprehensive explanation of why this candidate matches (or doesn't match) this job.

Respond ONLY with valid JSON:
{{
  "overall_fit": "Excellent/Good/Fair/Poor",
  "key_strengths": "Top 3-5 strengths of this match",
  "main_concerns": "Top 2-3 concerns or gaps",
  "detailed_explanation": "2-3 paragraph detailed explanation",
  "confidence_level": "High/Medium/Low"
}}"""

            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.4,
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
            await cache_service.cache_llm_explanation(job_id, candidate_id, result)

            logger.info("Match explanation generated and cached")
            return result

        except Exception as e:
            logger.error(f"Explanation failed: {e}")
            return {
                "overall_fit": "Unknown",
                "key_strengths": "Unable to analyze",
                "main_concerns": "Analysis failed",
                "detailed_explanation": f"Error: {str(e)}",
                "confidence_level": "Low",
            }


explanation_chain = ExplanationChain()
