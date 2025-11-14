import hashlib
import json
import io
import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache
from app.core.deps import get_cache_client, get_current_active_user, get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeRead
from app.schemas.search import (
    EnhancedSearchResponse,
    ResumeSearchResult,
    SearchMetadata,
)
from app.utils.embedding_generator import (
    calculate_similarity,
    generate_resume_embedding,
)
from app.utils.match_explainer import generate_match_reasons
from app.utils.export import export_search_results_csv, export_search_results_json
from common.logging import get_logger

router = APIRouter()

logger = get_logger(__name__)


def unwrap_resume_fields(resume):
    experience_list = []
    if resume.experience:
        if isinstance(resume.experience, dict) and "entries" in resume.experience:
            experience_list = resume.experience["entries"]
        elif isinstance(resume.experience, list):
            experience_list = resume.experience

    education_list = []
    if resume.education:
        if isinstance(resume.education, dict) and "entries" in resume.education:
            education_list = resume.education["entries"]
        elif isinstance(resume.education, list):
            education_list = resume.education

    # Create resume dict with unwrapped lists
    resume_dict = resume.__dict__.copy()
    resume_dict["experience"] = experience_list
    resume_dict["education"] = education_list

    return resume_dict


@router.get("/semantic", response_model=EnhancedSearchResponse)
async def semantic_search_enhanced(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results"),
    min_score: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum similarity score"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
    cache: RedisCache = Depends(get_cache_client),
):

    start_time = time.time()

    user_id = current_user.get("sub") or current_user.get("user_id")

    # Generate Cache Key
    cache_data = {
        "query": query.lower().strip(),
        "top_k": top_k,
        "min_score": min_score,
    }
    cache_key_hash = hashlib.md5(
        json.dumps(cache_data, sort_keys=True).encode()
    ).hexdigest()
    cache_key = f"user:{user_id}:search:semantic:{cache_key_hash}"

    # Try Cache First
    cached_result = await cache.get(cache_key)
    if cached_result:
        cache_time = time.time() - start_time
        logger.info(
            f"CACHE HIT: '{query}' returned in {cache_time:.3f}s (saved ~4.5s!)"
        )

        # Add cache metadata
        if isinstance(cached_result, dict):
            cached_result["cached"] = True
            cached_result["cache_time"] = round(cache_time, 3)

        return EnhancedSearchResponse(**cached_result)

    logger.info(f"Cache miss: '{query}' - computing fresh results...")
    logger.info(f"Semantic search: '{query}' (top_k={top_k}, min_score={min_score})")

    # Generate query embedding from search query
    query_words = query.split()
    query_data = {
        "full_name": query,
        "email": "",
        "phone": "",
        "location": "",
        "skills": {"search_query": query_words},
        "experience": [{"title": query, "company": "", "description": [query]}],
        "education": [{"degree": query, "institution": ""}],
        "total_experience_years": 0,
    }

    query_embedding = generate_resume_embedding(query_data)
    logger.info(
        f"Generated query embedding: dim={len(query_embedding)}, query='{query}'"
    )

    # Get all resumes with embeddings
    result = await db.execute(
        select(Resume).where(
            Resume.is_embedding_generated == True,
            Resume.is_deleted == False,
        )
    )

    resumes = result.scalars().all()
    logger.info(f"Found {len(resumes)} resumes with embeddings")

    # Log each resume
    for i, resume in enumerate(resumes):
        emb_status = (
            "None" if resume.embedding is None else f"dim={len(resume.embedding)}"
        )
        logger.info(
            f"  Resume {i+1}: {resume.filename} - embedding={emb_status}, is_embedding_generated={resume.is_embedding_generated}"
        )

    if not resumes:
        logger.warning("No resumes with embeddings found")
        empty_response = {
            "results": [],
            "metadata": {
                "total_results": 0,
                "query": query,
                "search_time_seconds": time.time() - start_time,
                "min_score_threshold": min_score,
                "top_k": top_k,
            },
        }
        return EnhancedSearchResponse(**empty_response)

    # Calculate similarity scores for ALL resumes
    similarities = []
    for resume in resumes:
        if resume.embedding is not None and len(resume.embedding) > 0:
            try:
                score = calculate_similarity(query_embedding, resume.embedding)
                similarities.append((resume, score))
                logger.info(f"  {resume.filename}: score={score:.3f}")
            except Exception as e:
                logger.error(f"  {resume.filename}: Error calculating similarity: {e}")
        else:
            logger.warning(
                f"  {resume.filename}: No embedding (embedding={resume.embedding})"
            )

    logger.info(f"Calculated {len(similarities)} similarity scores")

    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Filter by min_score
    filtered = [(resume, score) for resume, score in similarities if score >= min_score]
    logger.info(f"Filtered: {len(filtered)} resumes above threshold {min_score}")

    # Take top_k
    top_results = filtered[:top_k]

    logger.info(
        f"Found {len(filtered)} resumes above threshold {min_score}, "
        f"returning top {len(top_results)}"
    )

    # Build enhanced results
    enhanced_results = []
    for rank, (resume, score) in enumerate(top_results, start=1):
        # Generate match reasons
        reasons = generate_match_reasons(resume, query, score)

        # Unwrap experience and education
        resume_dict = unwrap_resume_fields(resume)

        # Create result
        enhanced_result = ResumeSearchResult(
            resume=ResumeRead.model_validate(resume_dict),
            similarity_score=round(score, 3),
            match_percentage=int(score * 100),
            match_reasons=reasons,
            rank=rank,
        )

        enhanced_results.append(enhanced_result)

        logger.info(
            f"  #{rank}: {resume.filename} "
            f"(score={score:.3f}, reasons={len(reasons)})"
        )

    # Calculate search time
    search_time = time.time() - start_time

    # Build Response

    response_dict = {
        "results": [r.model_dump() for r in enhanced_results],
        "metadata": {
            "total_results": len(enhanced_results),
            "query": query,
            "search_time_seconds": round(search_time, 3),
            "min_score_threshold": min_score,
            "top_k": top_k,
        },
        "cached": False,
    }

    # Cache the Result

    cache_success = await cache.set(cache_key, response_dict, ttl=3600)

    if cache_success:
        logger.info(f"Cached search results for: '{query}' (key: {cache_key[:30]}...)")
    else:
        logger.warning(f"Failed to cache results for: '{query}'")

    logger.info(
        f"Search completed in {search_time:.3f}s "
        f"(query='{query}', results={len(enhanced_results)})"
    )

    response = EnhancedSearchResponse(
        results=enhanced_results,
        metadata=SearchMetadata(
            total_results=len(enhanced_results),
            query=query,
            search_time_seconds=round(search_time, 3),
            min_score_threshold=min_score,
            top_k=top_k,
        ),
    )

    return response


@router.get("/similar/{resume_id}", response_model=List[ResumeRead])
async def find_similar_resumes(
    resume_id: uuid.UUID,
    top_k: int = Query(5, ge=1, le=20, description="Number of similar resumes"),
    min_score: float = Query(
        0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    logger.info(f"Finding similar resumes to: {resume_id}")

    # Get target resume
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.is_deleted == False)
    )

    target_resume = result.scalar_one_or_none()

    if not target_resume:
        logger.warning(f"Target resume not found: {resume_id}")
        return []

    # Check embedding
    if target_resume.embedding is None or len(target_resume.embedding) == 0:
        logger.warning("Target resume has no embedding")
        return []

    # Get all other resumes with embeddings
    result = await db.execute(
        select(Resume).where(
            Resume.id != resume_id,
            Resume.is_embedding_generated == True,
            Resume.is_deleted == False,
        )
    )

    resumes = result.scalars().all()

    # Calculate similarities
    similarities = []
    for resume in resumes:
        if resume.embedding is not None and len(resume.embedding) > 0:
            score = calculate_similarity(target_resume.embedding, resume.embedding)
            if score >= min_score:
                similarities.append((resume, score))

    # Sort by score descending
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Take top_k
    top_results = similarities[:top_k]

    logger.info(f"Found {len(top_results)} similar resumes")

    # Unwrap fields for each resume
    return [
        ResumeRead.model_validate(unwrap_resume_fields(resume))
        for resume, score in top_results
    ]


@router.get("/skills", response_model=List[ResumeRead])
async def search_by_skills(
    skills: str = Query(..., description="Comma-separated skills"),
    match_all: bool = Query(False, description="Require all skills"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    skill_list = [s.strip().lower() for s in skills.split(",")]

    logger.info(f"Skill search: {skill_list} (match_all={match_all})")

    # Get all resumes
    result = await db.execute(
        select(Resume).where(Resume.is_parsed == True, Resume.is_deleted == False)
    )

    resumes = result.scalars().all()

    matching_resumes = []

    for resume in resumes:
        if not resume.skills:
            continue

        # Get all skills from resume
        resume_skills = set()

        try:
            if isinstance(resume.skills, dict):
                for category_skills in resume.skills.values():
                    if isinstance(category_skills, list):
                        resume_skills.update([s.lower() for s in category_skills])
            elif isinstance(resume.skills, list):
                resume_skills.update([s.lower() for s in resume.skills])
        except Exception as e:
            logger.error(f"Error processing skills for resume {resume.id}: {e}")
            continue

        # Check match
        if match_all:
            if all(skill in resume_skills for skill in skill_list):
                matching_resumes.append(resume)
        else:
            if any(skill in resume_skills for skill in skill_list):
                matching_resumes.append(resume)

    logger.info(f"Found {len(matching_resumes)} matching resumes")

    # Unwrap fields for each resume
    return [
        ResumeRead.model_validate(unwrap_resume_fields(resume))
        for resume in matching_resumes
    ]


@router.get("/export")
async def export_search_results(
    query: str = Query(..., description="Search query"),
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results"),
    min_score: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum similarity score"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    logger.info(f"Export request: '{query}' format={format}")

    # Reuse the enhanced semantic search logic
    start_time = time.time()

    # Generate query embedding
    query_words = query.split()
    query_data = {
        "full_name": query,
        "skills": {"search_query": query_words},
        "experience": [{"title": query, "description": [query]}],
        "education": [],
        "total_experience_years": 0,
    }

    query_embedding = generate_resume_embedding(query_data)

    # Get all resumes with embeddings
    result = await db.execute(
        select(Resume).where(
            Resume.is_embedding_generated == True,
            Resume.is_deleted == False,
        )
    )

    resumes = result.scalars().all()

    if not resumes:
        # Return empty file
        if format == "csv":
            content = "No results found"
            media_type = "text/csv"
            filename = f"search_results_{query[:20]}.csv"
        else:
            content = json.dumps({"query": query, "total_results": 0, "results": []})
            media_type = "application/json"
            filename = f"search_results_{query[:20]}.json"

        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # Calculate similarities
    similarities = []
    for resume in resumes:
        if resume.embedding is not None and len(resume.embedding) > 0:
            score = calculate_similarity(query_embedding, resume.embedding)
            similarities.append((resume, score))

    # Sort and filter
    similarities.sort(key=lambda x: x[1], reverse=True)
    filtered = [(resume, score) for resume, score in similarities if score >= min_score]
    top_results = filtered[:top_k]

    # Build enhanced results
    enhanced_results = []
    for rank, (resume, score) in enumerate(top_results, start=1):
        reasons = generate_match_reasons(resume, query, score)
        resume_dict = unwrap_resume_fields(resume)
        enhanced_result = ResumeSearchResult(
            resume=ResumeRead.model_validate(resume_dict),
            similarity_score=round(score, 3),
            match_percentage=int(score * 100),
            match_reasons=reasons,
            rank=rank,
        )
        enhanced_results.append(enhanced_result)

    # Export based on format
    if format == "csv":
        content = export_search_results_csv(enhanced_results, query)
        media_type = "text/csv"
        filename = f"search_results_{query.replace(' ', '_')[:20]}.csv"
    else:  # json
        metadata = {
            "search_time_seconds": round(time.time() - start_time, 3),
            "min_score_threshold": min_score,
            "top_k": top_k,
        }
        content = export_search_results_json(enhanced_results, query, metadata)
        media_type = "application/json"
        filename = f"search_results_{query.replace(' ', '_')[:20]}.json"

    logger.info(f"Exported {len(enhanced_results)} results as {format}")

    # Stream response
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content.encode())),
        },
    )


@router.get("/cache/stats")
async def get_cache_stats(
    cache: RedisCache = Depends(get_cache_client),
    current_user=Depends(get_current_active_user),
):
    user_id = current_user.get("sub") or current_user.get("user_id")
    stats = await cache.get_stats()

    return {
        "user_id": str(user_id),
        "cache_enabled": stats.get("enabled", False),
        "total_keys": stats.get("keys", 0),
        "hit_rate": f"{stats.get('hit_rate', 0)}%",
        "hits": stats.get("hits", 0),
        "misses": stats.get("misses", 0),
        "message": "Cache is working!" if stats.get("enabled") else "Cache is disabled",
    }


@router.post("/cache/clear")
async def clear_user_cache(
    cache: RedisCache = Depends(get_cache_client),
    current_user=Depends(get_current_active_user),
):
    user_id = current_user.get("sub") or current_user.get("user_id")
    deleted_count = await cache.clear_user_cache(str(user_id))

    return {
        "message": f"Cleared {deleted_count} cached searches",
        "user_id": str(user_id),
        "deleted_keys": deleted_count,
    }
