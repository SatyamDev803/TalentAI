import ray
from typing import List, Dict, Any
import numpy as np
import time

from common.logging import get_logger
from app.utils.chroma_manager import ChromaManager
from app.services.embedding_service import embedding_service

logger = get_logger(__name__)


@ray.remote(num_cpus=0.5, memory=1024 * 1024 * 1024)  # 1GB memory
class VectorActor:

    def __init__(self):
        self.chroma_manager = None
        self.embedding_service = None
        self.total_searches = 0
        self.total_search_time = 0.0

        logger.info("VectorActor initialized (lazy loading ChromaDB)")

    def _ensure_initialized(self):

        if self.chroma_manager is None:
            try:
                self.chroma_manager = ChromaManager()
                self.embedding_service = embedding_service

                logger.info("VectorActor services initialized")
            except Exception as e:
                logger.error(f"Failed to initialize VectorActor services: {e}")
                raise

    async def generate_embedding(
        self, text: str, embedding_type: str = "resume"
    ) -> List[float]:

        self._ensure_initialized()

        try:
            if embedding_type == "job":
                embedding = await self.embedding_service.generate_job_embedding(
                    {"title": "", "description": text, "required_skills": []}
                )
            else:
                embedding = await self.embedding_service.generate_resume_embedding(
                    {"name": "", "summary": text, "skills": []}
                )

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def search_similar_candidates(
        self,
        job_embedding: List[float],
        top_k: int = 10,
        collection_name: str = "resume_embeddings",
    ) -> List[Dict[str, Any]]:

        self._ensure_initialized()
        start_time = time.time()

        try:
            collection = self.chroma_manager.get_or_create_collection(collection_name)

            results = collection.query(
                query_embeddings=[job_embedding],
                n_results=top_k,
                include=["embeddings", "metadatas", "distances"],
            )

            # Format results
            candidates = []
            if results and results["ids"] and results["ids"][0]:
                for idx, (candidate_id, distance, metadata) in enumerate(
                    zip(
                        results["ids"][0],
                        results["distances"][0],
                        results["metadatas"][0],
                    )
                ):
                    # Convert distance to similarity (assuming L2 distance)
                    similarity = 1 / (1 + distance)

                    candidates.append(
                        {
                            "rank": idx + 1,
                            "candidate_id": candidate_id,
                            "similarity_score": round(similarity, 4),
                            "metadata": metadata or {},
                        }
                    )

            # Track performance
            search_time = (time.time() - start_time) * 1000
            self.total_searches += 1
            self.total_search_time += search_time

            logger.info(
                f"Vector search found {len(candidates)} candidates in {search_time:.2f}ms"
            )

            return candidates

        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            return []

    async def search_similar_jobs(
        self,
        candidate_embedding: List[float],
        top_k: int = 10,
        collection_name: str = "job_embeddings",
    ) -> List[Dict[str, Any]]:

        self._ensure_initialized()
        start_time = time.time()

        try:
            collection = self.chroma_manager.get_or_create_collection(collection_name)

            results = collection.query(
                query_embeddings=[candidate_embedding],
                n_results=top_k,
                include=["embeddings", "metadatas", "distances"],
            )

            # Format results
            jobs = []
            if results and results["ids"] and results["ids"][0]:
                for idx, (job_id, distance, metadata) in enumerate(
                    zip(
                        results["ids"][0],
                        results["distances"][0],
                        results["metadatas"][0],
                    )
                ):
                    similarity = 1 / (1 + distance)

                    jobs.append(
                        {
                            "rank": idx + 1,
                            "job_id": job_id,
                            "similarity_score": round(similarity, 4),
                            "metadata": metadata or {},
                        }
                    )

            search_time = (time.time() - start_time) * 1000
            self.total_searches += 1
            self.total_search_time += search_time

            logger.info(f"Vector search found {len(jobs)} jobs in {search_time:.2f}ms")

            return jobs

        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            return []

    def compute_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:

        if not vec1 or not vec2:
            return 0.0

        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = float(dot_product / (norm1 * norm2))
            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        except Exception as e:
            logger.error(f"Cosine similarity computation failed: {e}")
            return 0.0

    def batch_similarity_search(
        self,
        embeddings: List[List[float]],
        top_k: int = 10,
        collection_name: str = "resume_embeddings",
    ) -> List[List[Dict[str, Any]]]:

        results = []
        for embedding in embeddings:
            try:
                similar = self.search_similar_candidates(
                    embedding, top_k, collection_name
                )
                results.append(similar)
            except Exception as e:
                logger.error(f"Batch search error: {e}")
                results.append([])

        return results

    def get_statistics(self) -> Dict[str, Any]:

        avg_time = (
            self.total_search_time / self.total_searches
            if self.total_searches > 0
            else 0.0
        )

        return {
            "total_searches": self.total_searches,
            "total_search_time_ms": round(self.total_search_time, 2),
            "avg_search_time_ms": round(avg_time, 2),
            "status": "healthy",
            "initialized": self.chroma_manager is not None,
        }
