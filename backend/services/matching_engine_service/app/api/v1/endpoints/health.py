from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import ray

from app.core.deps import get_db
from app.core.cache import cache_service
from app.services.llm_orchestrator import llm_orchestrator
from app.utils.chroma_manager import chroma_manager
from common.redis_client import redis_client
from common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "matching-engine-service",
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    results = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        results["database"] = {"status": "Connected", "type": "PostgreSQL"}
    except Exception as e:
        results["database"] = {"status": "Failed", "error": str(e)}

    # Redis
    try:
        await redis_client.ping()
        results["redis"] = {"status": "Connected"}
    except Exception as e:
        results["redis"] = {"status": "Failed", "error": str(e)}

    # Ray
    try:
        if ray.is_initialized():
            results["ray"] = {
                "status": "Initialized",
                "nodes": len(ray.nodes()),
                "cpus": ray.cluster_resources().get("CPU", 0),
            }
        else:
            results["ray"] = {"status": "Not initialized"}
    except Exception as e:
        results["ray"] = {"status": "Failed", "error": str(e)}

    # ChromaDB
    try:
        stats = chroma_manager.get_collection_stats("resume_embeddings")
        results["chromadb"] = {
            "status": "Connected",
            "resume_count": stats.get("document_count", 0),
        }
    except Exception as e:
        results["chromadb"] = {"status": "Failed", "error": str(e)}

    # LLM Providers
    try:
        llm_status = llm_orchestrator.get_provider_status()
        results["llm"] = {
            "status": "Ready",
            "active_provider": llm_status["active"],
            "available_providers": llm_status["available_providers"],
        }
    except Exception as e:
        results["llm"] = {"status": "Failed", "error": str(e)}

    # Cache
    try:
        cache_stats = await cache_service.get_detailed_stats()
        results["cache"] = {"status": "Connected", **cache_stats}
    except Exception as e:
        results["cache"] = {"status": "Failed", "error": str(e)}

    # Overall status
    all_passed = all("HEALTHY" in str(v.get("status", "")) for v in results.values())

    return {
        "overall_status": "HEALTHY" if all_passed else "DEGRADED",
        "components": results,
    }


# Cache endpoints
@router.get("/cache/stats")
async def get_cache_statistics():

    try:
        stats = await cache_service.get_detailed_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = Query(
        default="*", description="Pattern to clear 'vector_search_job:*' or '*'"
    )
):

    try:
        count = await cache_service.delete_pattern(pattern)
        return {
            "status": "success",
            "message": f"Cleared {count} cache entries",
            "pattern": pattern,
            "deleted_count": count,
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate/job/{job_id}")
async def invalidate_job_cache(job_id: str):

    try:
        deleted_count = await cache_service.invalidate_job_cache(job_id)
        return {
            "status": "success",
            "message": f"Invalidated cache for job {job_id}",
            "job_id": job_id,
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error(f"Job cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate/candidate/{candidate_id}")
async def invalidate_candidate_cache(candidate_id: str):

    try:
        deleted_count = await cache_service.invalidate_candidate_cache(candidate_id)
        return {
            "status": "success",
            "message": f"Invalidated cache for candidate {candidate_id}",
            "candidate_id": candidate_id,
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error(f"Candidate cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
