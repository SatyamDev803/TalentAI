from typing import List, Dict, Any
import time

from app.utils.chroma_manager import chroma_manager
from common.logging import get_logger

logger = get_logger(__name__)


class VectorQueryRouter:

    def __init__(self):
        self.chroma = chroma_manager

        # Performance tracking
        self.query_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "total_latency": 0.0,
            "avg_latency": 0.0,
        }

    def _update_stats(self, success: bool, latency_ms: float):
        self.query_stats["total"] += 1

        if success:
            self.query_stats["success"] += 1
            self.query_stats["total_latency"] += latency_ms
            self.query_stats["avg_latency"] = (
                self.query_stats["total_latency"] / self.query_stats["success"]
            )
        else:
            self.query_stats["failed"] += 1

    async def search_similar_resumes(
        self,
        job_text: str,
        top_k: int = 10,
        **kwargs,
    ) -> List[Dict[str, Any]]:

        start = time.time()
        try:
            results = self.chroma.search_similar_resumes(job_text, top_k)
            latency = (time.time() - start) * 1000
            self._update_stats(True, latency)

            logger.info(f"ChromaDB search: {len(results)} results in {latency:.2f}ms")
            return results

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._update_stats(False, latency)
            logger.error(f"ChromaDB search failed: {e}")
            return []

    async def search_similar_jobs(
        self, resume_text: str, top_k: int = 10, **kwargs
    ) -> List[Dict[str, Any]]:

        start = time.time()
        try:
            results = self.chroma.search_similar_jobs(resume_text, top_k)
            latency = (time.time() - start) * 1000
            self._update_stats(True, latency)

            logger.info(f"ChromaDB search: {len(results)} results in {latency:.2f}ms")
            return results

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._update_stats(False, latency)
            logger.error(f"ChromaDB search failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        total = self.query_stats["total"]
        success_rate = (self.query_stats["success"] / total * 100) if total > 0 else 0

        return {
            "vector_db": "chromadb",
            "total_queries": total,
            "successful_queries": self.query_stats["success"],
            "failed_queries": self.query_stats["failed"],
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(self.query_stats["avg_latency"], 2),
        }

    def reset_stats(self):
        self.query_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "total_latency": 0.0,
            "avg_latency": 0.0,
        }
        logger.info("Query statistics reset")


vector_query_router = VectorQueryRouter()
