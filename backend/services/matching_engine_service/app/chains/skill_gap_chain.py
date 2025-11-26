from typing import Dict, Any
import json
import google.generativeai as genai

from app.core.cache import cache_service
from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class SkillGapChain:

    def __init__(self):

        api_key = settings.google_api_key
        if not api_key:
            logger.warning("GOOGLE_API_KEY not configured")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    async def analyze(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        job_id: str = "unknown",
        candidate_id: str = "unknown",
        skip_cache: bool = False,
    ) -> Dict[str, Any]:

        if not skip_cache:
            cached_result = await cache_service.get_llm_skill_gap(job_id, candidate_id)
            if cached_result:
                logger.info(
                    f"Skill gap cache HIT for {job_id}-{candidate_id} (saved ~3s)"
                )
                return cached_result

        logger.info(
            f"Skill gap cache MISS for {job_id}-{candidate_id} - Running analysis..."
        )

        try:
            # Build prompt
            prompt = f"""You are an expert technical recruiter analyzing candidate-job fit.

Job Requirements:
Title: {job_data.get("title", "")}
Required Skills: {", ".join(job_data.get("required_skills", []))}
Description: {job_data.get("description", "")}

Candidate Profile:
Skills: {", ".join(candidate_data.get("skills", []))}
Experience: {candidate_data.get("years_experience", 0)} years
Summary: {candidate_data.get("summary", "")}

Analyze the skill gap and provide a detailed assessment.

Respond ONLY with valid JSON in this exact format:
{{
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "transferable_skills": ["skill5"],
  "skill_gap_percentage": 50.0,
  "analysis_summary": "Brief summary text"
}}

No other text, just the JSON."""

            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                ),
            )

            # Parse JSON response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())

            await cache_service.cache_llm_skill_gap(job_id, candidate_id, result)

            logger.info(
                f"Skill gap analysis completed and cached for {job_data.get('title')}"
            )
            return result

        except Exception as e:
            logger.error(f"Skill gap analysis failed: {e}")
            return {
                "matching_skills": [],
                "missing_skills": [],
                "transferable_skills": [],
                "skill_gap_percentage": 50.0,
                "analysis_summary": f"Analysis failed: {str(e)}",
            }


skill_gap_chain = SkillGapChain()
