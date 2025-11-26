from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.vector import HybridSearchRequest
from app.services.vector_search_service import vector_search_service
from app.core.deps import get_db
from common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/candidates/hybrid")
async def hybrid_search_candidates(
    request: HybridSearchRequest, db: AsyncSession = Depends(get_db)
):
    # combining vector + keyword matching
    try:
        job_data = {
            "title": request.job_title,
            "description": request.job_description,
            "required_skills": request.required_skills,
            "experience_level": request.experience_level,
            "location": request.location,
        }

        results = await vector_search_service.hybrid_search(
            query_data=job_data,
            search_type="candidates",
            top_k=request.top_k,
            vector_weight=request.vector_weight,
            keyword_weight=request.keyword_weight,
        )

        return {
            "search_type": "hybrid",
            "query": {
                "job_title": request.job_title,
                "skills": request.required_skills,
            },
            "weights": {
                "vector": request.vector_weight,
                "keyword": request.keyword_weight,
            },
            "total_found": len(results),
            "candidates": results,
        }

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
