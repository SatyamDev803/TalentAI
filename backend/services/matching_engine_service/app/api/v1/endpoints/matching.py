from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any
import asyncio
import hashlib
import time
import ray


from app.schemas.Batch import (
    BatchMatchRequest,
    BatchMatchResponse,
    CandidateMatchResult,
)
from app.services.vector_search_service import vector_search_service
from app.chains import chain_orchestrator
from app.actors.matcher_actor import MatcherActor
from app.actors.vector_actor import VectorActor
from common.logging import get_logger
from app.services.langgraph_matching import LangGraphMatchingWorkflow
from app.services.llm_orchestrator import llm_orchestrator

logger = get_logger(__name__)
router = APIRouter()


# Ray Batch Matching
@router.post("/batch", response_model=BatchMatchResponse, tags=["Matching"])
async def batch_match_candidates(request: BatchMatchRequest):
    """
    **Example Request:**
    ```
    {
        "job_data": {
            "id": "job_123",
            "title": "Python Developer",
            "description": "Build web apps",
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "experience_required": 3,
            "location": "San Francisco, CA",
            "salary_max": 120000,
            "remote_allowed": false
        },
        "candidates_data": [
            {
                "id": "cand_001",
                "name": "John Doe",
                "skills": ["Python", "Django", "React"],
                "total_experience": 5,
                "location": "San Francisco, CA",
                "expected_salary": 110000
            }
        ],
        "use_vector_search": false,
        "min_score_threshold": 60.0
    }
    ```

    **Returns:**
    - Candidates ranked by overall match score (descending)
    - Detailed breakdown: skills, experience, location, salary
    - Processing time and metadata
    """

    logger.info(
        f"Ray batch matching: job={request.job_data.get('id')}, "
        f"candidates={len(request.candidates_data)}"
    )

    start_time = time.time()

    try:
        job_data = request.job_data
        candidates_data = request.candidates_data

        if not job_data.get("id"):
            raise HTTPException(400, "job_data must include 'id' field")

        logger.info(f"Job: {job_data.get('title', 'Unknown')}")
        logger.info(f"Candidates: {len(candidates_data)}")

        # Vector Search
        vector_similarities = None

        if request.use_vector_search:
            try:
                logger.info("Running vector similarity search...")

                vector_actor = VectorActor.remote()

                job_text = (
                    f"{job_data.get('title', '')} {job_data.get('description', '')}"
                )
                job_embedding = await vector_actor.generate_embedding.remote(
                    job_text, embedding_type="job"
                )

                similar_candidates = (
                    await vector_actor.search_similar_candidates.remote(
                        job_embedding=job_embedding, top_k=len(candidates_data)
                    )
                )

                similarity_map = {
                    c["candidate_id"]: c["similarity_score"] for c in similar_candidates
                }

                vector_similarities = [
                    similarity_map.get(str(c.get("id")), 0.0) for c in candidates_data
                ]

                logger.info("Vector search complete")

            except Exception as e:
                logger.warning(f"Vector search failed: {e}, continuing without it")
                vector_similarities = None

        # Initialize ray actors, low memory
        # Smart actor allocation based on batch size
        if len(candidates_data) <= 5:
            num_actors = 1
            logger.info("Small batch: using 1 actor")
        elif len(candidates_data) <= 20:
            num_actors = 2
            logger.info("Medium batch: using 2 actors")
        else:
            num_actors = 4
            logger.info("Large batch: using 4 actors")

        weights = {"skill": 0.40, "experience": 0.30, "location": 0.15, "salary": 0.15}

        # Create actors with minimum resource requirements
        try:
            matcher_actors = [
                MatcherActor.options(
                    num_cpus=0.5,  # 0.5 CPU per actor
                    memory=128 * 1024 * 1024,  # 128MB RAM per actor
                ).remote(weights=weights, enable_vector=request.use_vector_search)
                for _ in range(num_actors)
            ]

            logger.info(
                f"Initialized {num_actors} Ray actors " f"(0.5 CPU, 128MB each)"
            )

        except Exception as e:
            logger.error(f"Failed to create Ray actors: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ray actor initialization failed: {str(e)}"
            )

        # Distribute candidates across actors
        actor_assignments = [[] for _ in range(num_actors)]
        actor_similarities = (
            [[] for _ in range(num_actors)] if vector_similarities else None
        )

        for idx, candidate in enumerate(candidates_data):
            actor_idx = idx % num_actors
            actor_assignments[actor_idx].append(candidate)

            if vector_similarities:
                actor_similarities[actor_idx].append(vector_similarities[idx])

        # Submit parallel matching tasks
        futures = []

        for actor_idx, actor_candidates in enumerate(actor_assignments):
            if actor_candidates:
                batch_similarities = (
                    actor_similarities[actor_idx] if actor_similarities else None
                )

                future = matcher_actors[actor_idx].batch_match.remote(
                    candidates=actor_candidates,
                    job=job_data,
                    vector_similarities=batch_similarities,
                )
                futures.append(future)

        logger.info(f"Submitted {len(futures)} parallel tasks to Ray")

        # Collect results
        all_results = []

        try:
            # Wait for all actors to complete (30 second timeout)
            logger.info(f"Waiting for {len(futures)} Ray tasks to complete...")

            batch_results = ray.get(futures, timeout=30)

            # Flatten results from all actors
            for batch in batch_results:
                all_results.extend(batch)

            logger.info(f"Collected {len(all_results)} match results from Ray")

        except ray.exceptions.GetTimeoutError:
            logger.error("Ray matching timeout after 30 seconds")
            raise HTTPException(
                status_code=504,
                detail="Batch matching timeout - try with fewer candidates",
            )
        except Exception as e:
            logger.error(f"Ray task execution failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ray task failed: {str(e)}")

        # Filter by minimum score
        if request.min_score_threshold:
            filtered_results = [
                r
                for r in all_results
                if r.get("overall_score", 0) >= request.min_score_threshold
            ]
            logger.info(
                f"Filtered {len(filtered_results)}/{len(all_results)} "
                f"candidates above threshold {request.min_score_threshold}"
            )
        else:
            filtered_results = all_results

        # Sort and Rank
        filtered_results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        for rank, result in enumerate(filtered_results, 1):
            result["rank"] = rank

        # Prepare the response
        elapsed_time = time.time() - start_time

        response = BatchMatchResponse(
            status="success",
            job_id=str(job_data.get("id")),
            total_candidates=len(candidates_data),
            matched_candidates=len(filtered_results),
            results=[CandidateMatchResult(**result) for result in filtered_results],
            processing_time_seconds=round(elapsed_time, 3),
            metadata={
                "num_actors": num_actors,
                "vector_search_enabled": request.use_vector_search,
                "min_score_threshold": request.min_score_threshold,
                "candidates_below_threshold": len(all_results) - len(filtered_results),
                "processing_method": "ray_parallel",
            },
        )

        logger.info(
            f"Ray batch matching complete: "
            f"{len(filtered_results)} matches in {elapsed_time:.2f}s"
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Batch matching failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch matching error: {str(e)}")


# Vector matching


@router.post("/match/candidates/vector", tags=["Vector Matching"])
async def match_candidates_by_vector(
    job_title: str = Query(..., description="Job title"),
    job_description: str = Query("", description="Job description"),
    required_skills: str = Query("", description="Comma-separated required skills"),
    top_k: int = Query(default=10, ge=1, le=50),
    add_llm_analysis: bool = Query(default=False),
    llm_depth: str = Query(default="top3", regex="^(top3|top5|all)$"),
):
    try:
        logger.info(
            f"Vector matching for: {job_title} (top_k={top_k}, llm={add_llm_analysis})"
        )

        skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
        job_id = hashlib.md5(job_title.encode()).hexdigest()[:16]

        job_data = {
            "id": job_id,
            "title": job_title,
            "description": job_description,
            "required_skills": skills_list,
            "seniority": "Mid-level",
        }

        candidates = await vector_search_service.search_candidates_by_job(
            job_data=job_data, top_k=top_k, min_similarity=0.5
        )

        if not candidates:
            return {
                "job_title": job_title,
                "total_matches": 0,
                "matches": [],
                "llm_analysis_enabled": False,
            }

        matches = []
        for candidate in candidates:
            match = {
                "rank": candidate["rank"],
                "candidate_id": candidate["candidate_id"],
                "similarity_score": candidate["similarity_score"],
                "metadata": candidate.get("metadata", {}),
                "match_scores": {
                    "overall_score": candidate["similarity_score"],
                    "skill_score": candidate["similarity_score"],
                    "experience_score": 0.8,
                },
            }
            matches.append(match)

        llm_results = {}
        if add_llm_analysis:
            analyze_count = {
                "top3": min(3, len(matches)),
                "top5": min(5, len(matches)),
                "all": len(matches),
            }.get(llm_depth, 3)

            logger.info(f"Running LLM analysis for top {analyze_count} matches")

            for match in matches[:analyze_count]:
                candidate_data = {
                    "id": match["candidate_id"],
                    "name": match["metadata"].get("name", "Candidate"),
                    "skills": (
                        match["metadata"].get("skills", "").split(",")
                        if match["metadata"].get("skills")
                        else []
                    ),
                    "years_experience": match["metadata"].get("years_experience", 0),
                    "summary": match["metadata"].get("summary", ""),
                }

                try:
                    result = await chain_orchestrator.full_analysis(
                        job_data=job_data,
                        candidate_data=candidate_data,
                        match_scores=match["match_scores"],
                    )
                    llm_results[match["candidate_id"]] = result
                except Exception as e:
                    logger.error(
                        f"LLM analysis failed for {match['candidate_id']}: {e}"
                    )
                    llm_results[match["candidate_id"]] = {"error": str(e)}

            logger.info(f"LLM analysis complete for {len(llm_results)} candidates")

        for match in matches:
            if match["candidate_id"] in llm_results:
                match["ai_insights"] = llm_results[match["candidate_id"]]

        return {
            "job_title": job_title,
            "total_matches": len(matches),
            "matches": matches,
            "llm_analysis_enabled": add_llm_analysis,
            "llm_analyzed_count": len(llm_results) if add_llm_analysis else 0,
        }

    except Exception as e:
        logger.error(f"Matching failed: {e}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@router.post("/match/jobs/vector", tags=["Vector Matching"])
async def match_jobs_by_vector(
    candidate_skills: str = Query(..., description="Comma-separated candidate skills"),
    candidate_experience: int = Query(
        ..., ge=0, le=50, description="Years of experience"
    ),
    candidate_summary: str = Query("", description="Professional summary"),
    desired_role: str = Query("", description="Desired job title"),
    top_k: int = Query(default=10, ge=1, le=50),
    add_llm_analysis: bool = Query(default=False),
    llm_depth: str = Query(default="top3", regex="^(top3|top5|all)$"),
):
    # Reverse Matching, Find jobs for a candidate using vector search
    try:
        logger.info(
            f"Reverse matching: Finding jobs for candidate with {candidate_experience}y exp"
        )

        skills_list = [s.strip() for s in candidate_skills.split(",") if s.strip()]

        candidate_data = {
            "skills": skills_list,
            "years_experience": candidate_experience,
            "summary": candidate_summary,
            "desired_role": desired_role,
        }

        jobs = await vector_search_service.search_jobs_by_candidate(
            candidate_data=candidate_data, top_k=top_k, min_similarity=0.5
        )

        if not jobs:
            return {
                "total_matches": 0,
                "matches": [],
                "message": "No matching jobs found. Job embeddings may not be indexed yet.",
                "llm_analysis_enabled": False,
            }

        matches = []
        for job in jobs:
            match = {
                "rank": job["rank"],
                "job_id": job["job_id"],
                "similarity_score": job["similarity_score"],
                "job_metadata": job.get("metadata", {}),
                "match_scores": {
                    "overall_score": job["similarity_score"],
                    "skill_score": job["similarity_score"],
                    "experience_score": 0.8,
                },
            }
            matches.append(match)

        llm_results = {}
        if add_llm_analysis:
            analyze_count = {
                "top3": min(3, len(matches)),
                "top5": min(5, len(matches)),
                "all": len(matches),
            }.get(llm_depth, 3)

            logger.info(f"Running LLM analysis for top {analyze_count} job matches...")

            for match in matches[:analyze_count]:
                job_data = {
                    "title": match["job_metadata"].get("title", "Unknown Job"),
                    "description": match["job_metadata"].get("description", ""),
                    "required_skills": (
                        match["job_metadata"].get("required_skills", "").split(",")
                        if match["job_metadata"].get("required_skills")
                        else []
                    ),
                    "seniority": match["job_metadata"].get("seniority", "Mid-level"),
                }

                try:
                    result = await chain_orchestrator.full_analysis(
                        job_data=job_data,
                        candidate_data=candidate_data,
                        match_scores=match["match_scores"],
                    )
                    llm_results[match["job_id"]] = result
                except Exception as e:
                    logger.error(f"LLM analysis failed for job {match['job_id']}: {e}")
                    llm_results[match["job_id"]] = {"error": str(e)}

        for match in matches:
            if match["job_id"] in llm_results:
                match["ai_insights"] = llm_results[match["job_id"]]

        return {
            "candidate_experience": candidate_experience,
            "total_matches": len(matches),
            "matches": matches,
            "llm_analysis_enabled": add_llm_analysis,
            "llm_analyzed_count": len(llm_results) if add_llm_analysis else 0,
        }

    except Exception as e:
        logger.error(f"Reverse matching failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Reverse matching failed: {str(e)}"
        )


@router.post("/match/batch/vector", tags=["Vector Matching"])
async def batch_match_vector(
    batch_request: Dict[str, Any] = Body(
        ...,
        example={
            "jobs": [
                {
                    "id": "job1",
                    "title": "Python Developer",
                    "required_skills": ["Python", "Django"],
                },
                {
                    "id": "job2",
                    "title": "Data Scientist",
                    "required_skills": ["Python", "ML", "Pandas"],
                },
            ],
            "top_k_per_job": 5,
            "add_llm_analysis": False,
        },
    )
):
    try:
        jobs = batch_request.get("jobs", [])
        top_k = batch_request.get("top_k_per_job", 10)

        if not jobs:
            raise HTTPException(400, "No jobs provided")
        if len(jobs) > 20:
            raise HTTPException(400, "Maximum 20 jobs per batch")

        logger.info(f"Vector batch matching {len(jobs)} jobs...")

        tasks = []
        for job in jobs:
            job_data = {
                "title": job.get("title", ""),
                "description": job.get("description", ""),
                "required_skills": job.get("required_skills", []),
                "seniority": job.get("seniority", "Mid-level"),
            }

            task = vector_search_service.search_candidates_by_job(
                job_data=job_data, top_k=top_k, min_similarity=0.5
            )
            tasks.append((job.get("id", f"job_{len(tasks)}"), task))

        results = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        batch_results = []
        for (job_id, _), candidates in zip(tasks, results):
            if isinstance(candidates, Exception):
                batch_results.append(
                    {
                        "job_id": job_id,
                        "status": "error",
                        "error": str(candidates),
                        "matches": [],
                    }
                )
            else:
                batch_results.append(
                    {
                        "job_id": job_id,
                        "status": "success",
                        "total_matches": len(candidates),
                        "matches": candidates,
                    }
                )

        logger.info(
            f"Vector batch matching complete: {len(batch_results)} jobs processed"
        )

        return {
            "total_jobs": len(jobs),
            "successful": sum(1 for r in batch_results if r["status"] == "success"),
            "failed": sum(1 for r in batch_results if r["status"] == "error"),
            "results": batch_results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch matching failed: {e}")
        raise HTTPException(500, f"Batch matching failed: {str(e)}")


@router.post("/match/candidates/langgraph", tags=["LangGraph"])
async def match_candidates_with_langgraph(
    job_title: str = Query(..., description="Job title"),
    job_description: str = Query("", description="Job description"),
    required_skills: str = Query("", description="Comma-separated required skills"),
    top_k: int = Query(default=5, ge=1, le=20),
    use_cache: bool = Query(default=True, description="Enable caching"),
):
    """LangGraph Multi-Step Reasoning, for advanced candidate matching"""
    try:
        logger.info(f"LangGraph matching for: {job_title} (top_k={top_k})")

        skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
        job_id = hashlib.md5(job_title.encode()).hexdigest()[:16]

        job_data = {
            "id": job_id,
            "title": job_title,
            "description": job_description,
            "required_skills": skills_list,
            "experience_level": "3+ years",
            "seniority": "Mid-level",
        }

        candidates = await vector_search_service.search_candidates_by_job(
            job_data=job_data, top_k=top_k, min_similarity=0.5, use_cache=use_cache
        )

        if not candidates:
            return {
                "job_title": job_title,
                "total_matches": 0,
                "matches": [],
                "workflow_type": "langgraph",
            }

        langgraph_workflow = LangGraphMatchingWorkflow(llm_orchestrator)

        matches = []
        for candidate in candidates:
            candidate_data = {
                "id": candidate["candidate_id"],
                "name": candidate.get("metadata", {}).get("name", "Candidate"),
                "skills": (
                    candidate.get("metadata", {}).get("skills", "").split(",")
                    if candidate.get("metadata", {}).get("skills")
                    else []
                ),
                "total_experience": candidate.get("metadata", {}).get(
                    "years_experience", 0
                ),
                "summary": candidate.get("metadata", {}).get("summary", ""),
            }

            cache_key = f"langgraph:{job_id}:{candidate['candidate_id']}"

            if use_cache:
                from app.core.cache import cache_service

                cached_result = await cache_service.get(cache_key)
                if cached_result:
                    logger.info(f"LangGraph cache HIT for {candidate['candidate_id']}")
                    matches.append(cached_result)
                    continue

            logger.info(f"Running LangGraph for {candidate['candidate_id']}")

            try:
                workflow_result = await langgraph_workflow.run_workflow(
                    job_data=job_data,
                    candidate_data=candidate_data,
                    vector_similarity=candidate["similarity_score"],
                )

                match = {
                    "rank": candidate["rank"],
                    "candidate_id": candidate["candidate_id"],
                    "similarity_score": candidate["similarity_score"],
                    "metadata": candidate.get("metadata", {}),
                    "langgraph_analysis": workflow_result,
                }

                if use_cache:
                    await cache_service.set(cache_key, match, ttl=3600)

                matches.append(match)

            except Exception as e:
                logger.error(
                    f"LangGraph workflow failed for {candidate['candidate_id']}: {e}"
                )
                matches.append(
                    {
                        "rank": candidate["rank"],
                        "candidate_id": candidate["candidate_id"],
                        "similarity_score": candidate["similarity_score"],
                        "metadata": candidate.get("metadata", {}),
                        "langgraph_analysis": {"error": str(e), "fallback": True},
                    }
                )

        logger.info(f"LangGraph analysis complete for {len(matches)} candidates")

        return {
            "job_title": job_title,
            "total_matches": len(matches),
            "matches": matches,
            "workflow_type": "langgraph",
            "cache_enabled": use_cache,
        }

    except Exception as e:
        logger.error(f"LangGraph matching failed: {e}")
        raise HTTPException(500, f"LangGraph matching failed: {str(e)}")
