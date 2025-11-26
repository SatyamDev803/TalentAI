import ray
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time

from common.logging import get_logger

logger = get_logger(__name__)


@ray.remote(num_cpus=0.5, memory=256 * 1024 * 1024)
class MatcherActor:

    def __init__(
        self,
        weights: Dict[str, float],
        enable_ml: bool = False,  # ML not implemented yet
        enable_vector: bool = False,  # Vector scoring optional
    ):

        # Validate and normalize weights
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            logger.warning(f"Weights sum to {weight_sum}, normalizing...")
            self.weights = {k: v / weight_sum for k, v in weights.items()}
        else:
            self.weights = weights

        self.enable_ml = enable_ml
        self.enable_vector = enable_vector

        # Performance tracking
        self.total_matches = 0
        self.total_processing_time = 0.0

        logger.info(
            f"MatcherActor initialized - "
            f"Weights: {self.weights}, "
            f"ML: {enable_ml}, Vector: {enable_vector}"
        )

    def compute_skill_score(
        self, candidate_skills: List[str], job_skills: List[str]
    ) -> Dict[str, Any]:

        if not job_skills:
            return {
                "score": 100.0,
                "matching": [],
                "missing": [],
                "extra": candidate_skills,
                "match_ratio": 1.0,
            }

        if not candidate_skills:
            return {
                "score": 0.0,
                "matching": [],
                "missing": job_skills,
                "extra": [],
                "match_ratio": 0.0,
            }

        # Normalize skills
        cand_skills_lower = {s.lower().strip() for s in candidate_skills}
        job_skills_lower = {s.lower().strip() for s in job_skills}

        # Calculate overlap
        matching_skills = cand_skills_lower.intersection(job_skills_lower)
        missing_skills = job_skills_lower - cand_skills_lower
        extra_skills = cand_skills_lower - job_skills_lower

        match_ratio = len(matching_skills) / len(job_skills_lower)

        # Base score from matching ratio
        base_score = match_ratio * 100

        # Bonus for extra skills (capped at 20%)
        bonus = min(len(extra_skills) * 5, 20)

        final_score = min(base_score + bonus, 100.0)

        return {
            "score": round(final_score, 2),
            "matching": list(matching_skills),
            "missing": list(missing_skills),
            "extra": list(extra_skills),
            "match_ratio": round(match_ratio, 4),
            "bonus": bonus,
        }

    def compute_experience_score(
        self, candidate_exp: float, required_exp: float
    ) -> Dict[str, Any]:

        if required_exp == 0:
            return {
                "score": 100.0,
                "status": "no_requirement",
                "gap": 0,
                "overqualified": False,
            }

        gap = candidate_exp - required_exp

        if candidate_exp >= required_exp:
            # Meets or exceeds requirement
            if gap <= 2:
                score = 100.0
                status = "perfect_match"
            elif gap <= 5:
                score = 95.0
                status = "slightly_overqualified"
            else:
                # Significantly overqualified
                penalty = min((gap - 5) * 2, 15)
                score = max(85.0, 100 - penalty)
                status = "overqualified"

            return {
                "score": round(score, 2),
                "status": status,
                "gap": round(gap, 2),
                "overqualified": gap > 2,
            }
        else:
            # Under-qualified
            ratio = candidate_exp / required_exp
            score = ratio * 100

            return {
                "score": round(score, 2),
                "status": "underqualified",
                "gap": round(gap, 2),
                "overqualified": False,
            }

    def compute_location_score(
        self, candidate_loc: str, job_loc: str, remote_ok: bool = False
    ) -> Dict[str, Any]:

        if remote_ok:
            return {
                "score": 100.0,
                "match_type": "remote_allowed",
                "exact_match": False,
            }

        if not candidate_loc or not job_loc:
            return {
                "score": 50.0,
                "match_type": "insufficient_data",
                "exact_match": False,
            }

        cand_loc_lower = candidate_loc.lower().strip()
        job_loc_lower = job_loc.lower().strip()

        # Exact match
        if cand_loc_lower == job_loc_lower:
            return {"score": 100.0, "match_type": "exact", "exact_match": True}

        # City match
        if cand_loc_lower in job_loc_lower or job_loc_lower in cand_loc_lower:
            return {"score": 80.0, "match_type": "city", "exact_match": False}

        # Country/State match
        cand_parts = cand_loc_lower.split(",")
        job_parts = job_loc_lower.split(",")

        if len(cand_parts) > 1 and len(job_parts) > 1:
            if cand_parts[-1].strip() == job_parts[-1].strip():
                return {"score": 60.0, "match_type": "region", "exact_match": False}

        # No match
        return {"score": 30.0, "match_type": "no_match", "exact_match": False}

    def compute_salary_score(
        self, candidate_exp_salary: float, job_salary: float, tolerance: float = 0.2
    ) -> Dict[str, Any]:

        if job_salary == 0:
            return {
                "score": 100.0,
                "status": "no_budget_specified",
                "within_range": True,
            }

        if candidate_exp_salary == 0:
            return {
                "score": 50.0,
                "status": "no_expectation_specified",
                "within_range": False,
            }

        ratio = candidate_exp_salary / job_salary

        # Perfect match within tolerance
        if 1 - tolerance <= ratio <= 1 + tolerance:
            return {
                "score": 100.0,
                "status": "within_budget",
                "ratio": round(ratio, 4),
                "within_range": True,
            }

        # Candidate expects more
        if ratio > 1:
            overage = ratio - 1
            penalty = min(overage * 100, 80)
            score = max(20.0, 100 - penalty)

            return {
                "score": round(score, 2),
                "status": "over_budget",
                "ratio": round(ratio, 4),
                "within_range": False,
                "overage_pct": round(overage * 100, 2),
            }
        else:
            # Candidate expects less
            return {
                "score": 90.0,
                "status": "under_budget",
                "ratio": round(ratio, 4),
                "within_range": True,
            }

    def compute_overall_score(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        vector_similarity: float = 0.0,
    ) -> Dict[str, Any]:

        start_time = time.time()

        try:
            # Extract candidate data
            candidate_skills = candidate.get("skills", [])
            candidate_exp = candidate.get("total_experience", 0)
            candidate_loc = candidate.get("location", "")
            candidate_salary = candidate.get("expected_salary", 0)

            # Extract job data
            job_skills = job.get("required_skills", [])
            required_exp = job.get("experience_required", 0)
            job_loc = job.get("location", "")
            job_salary = job.get("salary_max", 0)
            remote_ok = job.get("remote_allowed", False)

            # Compute individual scores
            skill_result = self.compute_skill_score(candidate_skills, job_skills)
            exp_result = self.compute_experience_score(candidate_exp, required_exp)
            loc_result = self.compute_location_score(candidate_loc, job_loc, remote_ok)
            sal_result = self.compute_salary_score(candidate_salary, job_salary)

            # Compute weighted overall score
            overall = (
                skill_result["score"] * self.weights["skill"]
                + exp_result["score"] * self.weights["experience"]
                + loc_result["score"] * self.weights["location"]
                + sal_result["score"] * self.weights["salary"]
            )

            # Track performance
            processing_time = (time.time() - start_time) * 1000
            self.total_matches += 1
            self.total_processing_time += processing_time

            return {
                "candidate_id": str(candidate.get("id")),
                "job_id": str(job.get("id")),
                "overall_score": round(overall, 2),
                "breakdown": {
                    "skill": skill_result,
                    "experience": exp_result,
                    "location": loc_result,
                    "salary": sal_result,
                },
                "vector_similarity": (
                    round(vector_similarity, 4) if vector_similarity else None
                ),
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": round(processing_time, 2),
            }

        except Exception as e:
            logger.error(f"Error in compute_overall_score: {e}", exc_info=True)
            return {
                "candidate_id": str(candidate.get("id", "unknown")),
                "job_id": str(job.get("id", "unknown")),
                "overall_score": 0.0,
                "error": str(e),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }

    def batch_match(
        self,
        candidates: List[Dict[str, Any]],
        job: Dict[str, Any],
        vector_similarities: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:

        results = []

        for idx, candidate in enumerate(candidates):
            try:
                # Get vector similarity if provided
                vector_sim = (
                    vector_similarities[idx]
                    if vector_similarities and idx < len(vector_similarities)
                    else 0.0
                )

                result = self.compute_overall_score(candidate, job, vector_sim)
                results.append(result)

            except Exception as e:
                logger.error(f"Error matching candidate {candidate.get('id')}: {e}")
                results.append(
                    {
                        "candidate_id": str(candidate.get("id", "unknown")),
                        "job_id": str(job.get("id", "unknown")),
                        "overall_score": 0.0,
                        "error": str(e),
                        "computed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

        # Sort by score descending
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        # Add ranks
        for rank, result in enumerate(results, 1):
            result["rank"] = rank

        logger.info(f"Batch match complete: {len(results)} candidates processed")
        return results

    def get_statistics(self) -> Dict[str, Any]:

        avg_time = (
            self.total_processing_time / self.total_matches
            if self.total_matches > 0
            else 0.0
        )

        return {
            "total_matches": self.total_matches,
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "avg_processing_time_ms": round(avg_time, 2),
            "weights": self.weights,
            "ml_enabled": self.enable_ml,
            "vector_enabled": self.enable_vector,
            "status": "healthy",
        }
