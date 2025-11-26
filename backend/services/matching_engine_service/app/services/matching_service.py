import ray
from typing import List, Dict, Any, Optional
from uuid import UUID
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.logging import get_logger
from app.actors.matcher_actor import MatcherActor
from app.actors.vector_actor import VectorActor
from app.services.llm_orchestrator import llm_orchestrator
from app.core.cache import cache_service
from app.core.config import settings
from app.models.match_score import (
    MatchScore as MatchScoreModel,
    QualityTier,
    Recommendation,
)

logger = get_logger(__name__)


class ScoreCalculator:

    @staticmethod
    def classify_quality_tier(score: float) -> QualityTier:

        if score >= 85:
            return QualityTier.TIER_1
        elif score >= 70:
            return QualityTier.TIER_2
        elif score >= 55:
            return QualityTier.TIER_3
        elif score >= 40:
            return QualityTier.TIER_4
        else:
            return QualityTier.TIER_5

    @staticmethod
    def get_recommendation(score: float) -> Recommendation:

        if score >= 85:
            return Recommendation.STRONG_HIRE
        elif score >= 70:
            return Recommendation.HIRE
        elif score >= 55:
            return Recommendation.CONSIDER
        else:
            return Recommendation.PASS

    @staticmethod
    def compute_confidence(breakdown: Dict[str, float]) -> float:

        scores = list(breakdown.values())
        if not scores:
            return 0.5

        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Normalize variance to confidence (0-1)
        confidence = max(0.0, min(1.0, 1 - (variance / 2500)))

        return round(confidence, 4)


class MatchingService:

    def __init__(self):

        self.score_calculator = ScoreCalculator()
        self.num_matcher_actors = settings.ray_num_cpus
        self.matcher_actors = []
        self.vector_actor = None
        self._init_actors()

    def _init_actors(self):

        try:
            # Create matcher actors
            weights = settings.matching_weights
            for i in range(self.num_matcher_actors):
                actor = MatcherActor.remote(weights)
                self.matcher_actors.append(actor)

            # Create vector actor
            self.vector_actor = VectorActor.remote()

            logger.info(
                f"Initialized {self.num_matcher_actors} MatcherActors, 1 VectorActor"
            )
            logger.info(
                f"LLM orchestrator available with provider: {llm_orchestrator.active_provider.value}"
            )
        except Exception as e:
            logger.error(f"Error initializing actors: {e}")
            raise

    async def match_candidates_for_job(
        self,
        job: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        include_explanation: bool = False,
        min_score: float = 0.0,
        db: Optional[AsyncSession] = None,
        ray_task_id: Optional[str] = None,
        chroma_used: bool = False,
    ) -> List[Dict[str, Any]]:

        start_time = time.time()

        if not candidates:
            logger.warning("No candidates provided for matching")
            return []

        # Validate required fields
        if "id" not in job:
            raise ValueError("Job must have 'id' field")

        # Split candidates across actors
        batch_size = max(1, len(candidates) // self.num_matcher_actors)
        candidate_batches = [
            candidates[i : i + batch_size]
            for i in range(0, len(candidates), batch_size)
        ]

        # Distribute work to actors
        futures = []
        for i, batch in enumerate(candidate_batches):
            actor = self.matcher_actors[i % len(self.matcher_actors)]
            future = actor.batch_match.remote(batch, job)
            futures.append(future)

        # Collect results
        try:
            batch_results = ray.get(futures)
            all_matches = []
            for batch_result in batch_results:
                all_matches.extend(batch_result)
        except Exception as e:
            logger.error(f"Ray actor execution failed: {e}")
            return []

        # Filter by min score
        filtered_matches = [
            match for match in all_matches if match["overall_score"] >= min_score
        ]

        # Sort by score
        filtered_matches.sort(key=lambda x: x["overall_score"], reverse=True)

        # Add quality tier and recommendation
        for match in filtered_matches:
            tier = self.score_calculator.classify_quality_tier(match["overall_score"])
            recommendation = self.score_calculator.get_recommendation(
                match["overall_score"]
            )
            confidence = self.score_calculator.compute_confidence(match["breakdown"])

            match["quality_tier"] = tier.value
            match["recommendation"] = recommendation.value
            match["confidence"] = confidence
            match["_tier_enum"] = tier  # Store enum for DB
            match["_recommendation_enum"] = recommendation  # Store enum for DB

        # Generate explanations if requested
        if include_explanation and filtered_matches:
            top_matches = filtered_matches[:10]

            for match in top_matches:
                try:
                    candidate = next(
                        (
                            c
                            for c in candidates
                            if str(c.get("id")) == match["candidate_id"]
                        ),
                        None,
                    )

                    if not candidate:
                        logger.warning(f"Candidate {match['candidate_id']} not found")
                        continue

                    explanation_result = (
                        await llm_orchestrator.generate_match_explanation(
                            job_data=job,
                            candidate_data=candidate,
                            match_scores={
                                "overall_score": match["overall_score"],
                                "skill_score": match["breakdown"]["skill"],
                                "experience_score": match["breakdown"]["experience"],
                            },
                        )
                    )

                    # Extract explanation components
                    if isinstance(explanation_result, dict):
                        match["explanation"] = explanation_result.get("explanation", "")
                        match["strengths"] = explanation_result.get("strengths", "")
                        match["gaps"] = explanation_result.get("gaps", "")
                    else:
                        match["explanation"] = str(explanation_result)
                        match["strengths"] = ""
                        match["gaps"] = ""

                except Exception as e:
                    logger.warning(f"Failed to generate explanation for match: {e}")
                    match["explanation"] = "Explanation generation failed"
                    match["strengths"] = ""
                    match["gaps"] = ""

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Add metadata to matches
        for match in filtered_matches:
            match["ray_task_id"] = ray_task_id
            match["chroma_used"] = chroma_used
            match["processing_time_ms"] = processing_time_ms

        # Persist to database
        if db:
            await self._persist_matches(filtered_matches, db)

        logger.info(
            f"Matched {len(filtered_matches)} candidates in {processing_time_ms}ms"
        )

        return filtered_matches

    async def _persist_matches(self, matches: List[Dict[str, Any]], db: AsyncSession):

        try:
            persisted_count = 0

            for match in matches:
                try:
                    # Parse UUIDs
                    candidate_id = UUID(match["candidate_id"])
                    job_id = UUID(match["job_id"])

                    # Check if match already exists (deduplication)
                    stmt = select(MatchScoreModel).where(
                        MatchScoreModel.candidate_id == candidate_id,
                        MatchScoreModel.job_id == job_id,
                    )
                    result = await db.execute(stmt)
                    existing_match = result.scalar_one_or_none()

                    if existing_match:
                        # Update existing match with new scores
                        existing_match.overall_score = match["overall_score"]
                        existing_match.skill_score = match["breakdown"]["skill"]
                        existing_match.experience_score = match["breakdown"][
                            "experience"
                        ]
                        existing_match.location_score = match["breakdown"]["location"]
                        existing_match.salary_score = match["breakdown"]["salary"]
                        existing_match.ml_quality_tier = match.get(
                            "_tier_enum", QualityTier.TIER_3
                        )
                        existing_match.ml_confidence = match.get("confidence")
                        existing_match.recommendation = match.get(
                            "_recommendation_enum", Recommendation.CONSIDER
                        )
                        existing_match.explanation = match.get("explanation", "")
                        existing_match.strengths = match.get("strengths", "")
                        existing_match.gaps = match.get("gaps", "")
                        existing_match.ray_task_id = match.get("ray_task_id")
                        existing_match.chroma_used = match.get("chroma_used", False)
                        existing_match.processing_time_ms = match.get(
                            "processing_time_ms"
                        )

                        logger.debug(
                            f"Updated existing match: {candidate_id} <-> {job_id}"
                        )
                    else:
                        # Create new match record
                        match_record = MatchScoreModel(
                            candidate_id=candidate_id,
                            job_id=job_id,
                            overall_score=match["overall_score"],
                            skill_score=match["breakdown"]["skill"],
                            experience_score=match["breakdown"]["experience"],
                            location_score=match["breakdown"]["location"],
                            salary_score=match["breakdown"]["salary"],
                            ml_quality_tier=match.get("_tier_enum", QualityTier.TIER_3),
                            ml_confidence=match.get("confidence"),
                            explanation=match.get("explanation", ""),
                            strengths=match.get("strengths", ""),
                            gaps=match.get("gaps", ""),
                            recommendation=match.get(
                                "_recommendation_enum", Recommendation.CONSIDER
                            ),
                            ray_task_id=match.get("ray_task_id"),
                            chroma_used=match.get("chroma_used", False),
                            processing_time_ms=match.get("processing_time_ms"),
                        )
                        db.add(match_record)
                        persisted_count += 1

                except ValueError as e:
                    logger.error(f"Invalid UUID in match: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing match: {e}")
                    continue

            await db.commit()
            logger.info(f"Persisted {persisted_count} new matches to database")

        except Exception as e:
            logger.error(f"Error persisting matches: {e}")
            await db.rollback()
            raise

    async def get_cached_matches(
        self, job_id: UUID, db: AsyncSession, min_score: float = 0.0, limit: int = 50
    ) -> List[MatchScoreModel]:

        try:
            from datetime import datetime, timezone

            stmt = (
                select(MatchScoreModel)
                .where(
                    MatchScoreModel.job_id == job_id,
                    MatchScoreModel.overall_score >= min_score,
                    MatchScoreModel.expires_at > datetime.now(timezone.utc),
                )
                .order_by(MatchScoreModel.overall_score.desc())
                .limit(limit)
            )

            result = await db.execute(stmt)
            matches = result.scalars().all()

            logger.info(f"Retrieved {len(matches)} cached matches for job {job_id}")
            return list(matches)

        except Exception as e:
            logger.error(f"Error retrieving cached matches: {e}")
            return []

    async def invalidate_job_cache(self, job_id: UUID) -> int:

        try:

            # Invalidate both match cache and vector search cache
            pattern1 = f"match:job:{job_id}:*"
            pattern2 = f"vector_search:*job_id={job_id}*"

            count1 = await cache_service.invalidate(pattern1)
            count2 = await cache_service.invalidate(pattern2)

            total = count1 + count2
            logger.info(f"Invalidated {total} cache entries for job {job_id}")

            return total

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0


matching_service = MatchingService()
