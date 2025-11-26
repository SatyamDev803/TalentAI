import asyncio
import time
from typing import Dict, Any

from .skill_gap_chain import skill_gap_chain
from .explanation_chain import explanation_chain
from .recommendation_chain import recommendation_chain
from common.logging import get_logger

logger = get_logger(__name__)


class ChainOrchestrator:

    def __init__(self):
        # Gemini free tier: 10 requests/minute = 6 seconds between calls
        # Add 1 second buffer for safety
        self.min_delay_between_calls = 7.0
        self.last_call_time = 0

    async def _rate_limit_wait(self):
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time

        if time_since_last_call < self.min_delay_between_calls:
            wait_time = self.min_delay_between_calls - time_since_last_call
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s before next LLM call")
            await asyncio.sleep(wait_time)

        self.last_call_time = time.time()

    async def full_analysis(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        match_scores: Dict[str, Any],
        job_id: str = "unknown",
        candidate_id: str = "unknown",
        skip_cache: bool = False,
    ) -> Dict[str, Any]:

        logger.info(
            f"Starting full analysis for job={job_id}, candidate={candidate_id}"
        )

        try:
            # Chain 1 Skill Gap Analysis
            await self._rate_limit_wait()
            skill_gap = await skill_gap_chain.analyze(
                job_data,
                candidate_data,
                job_id=job_id,
                candidate_id=candidate_id,
                skip_cache=skip_cache,
            )

            # Chain 2 Match Explanation
            await self._rate_limit_wait()
            explanation = await explanation_chain.explain(
                job_data,
                candidate_data,
                match_scores,
                job_id=job_id,
                candidate_id=candidate_id,
                skip_cache=skip_cache,
            )

            # Chain 3 Hiring Recommendation
            await self._rate_limit_wait()
            recommendation = await recommendation_chain.recommend(
                job_data,
                candidate_data,
                match_scores,
                skill_gap,
                job_id=job_id,
                candidate_id=candidate_id,
                skip_cache=skip_cache,
            )

            logger.info("Full analysis complete")

            return {
                "skill_gap_analysis": skill_gap,
                "match_explanation": explanation,
                "hiring_recommendation": recommendation,
                "metadata": {
                    "cached": not skip_cache,
                    "timestamp": time.time(),
                },
            }

        except Exception as e:
            logger.error(f"Full analysis failed: {e}")
            return {
                "error": str(e),
                "skill_gap_analysis": {},
                "match_explanation": {},
                "hiring_recommendation": {},
            }


chain_orchestrator = ChainOrchestrator()
