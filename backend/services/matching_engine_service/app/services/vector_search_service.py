from typing import List, Dict, Any, Optional
import time
import hashlib
import json

from app.services.embedding_service import embedding_service
from app.core.cache import cache_service
from app.utils.chroma_manager import chroma_manager
from common.logging import get_logger

logger = get_logger(__name__)


class VectorSearchService:

    def __init__(self):
        self.embedding_service = embedding_service
        self.chroma_manager = chroma_manager
        logger.info("VectorSearchService initialized")

    def _generate_cache_key(self, data: Dict[str, Any], prefix: str = "") -> str:

        try:
            # Sort keys for deterministic hashing
            json_str = json.dumps(data, sort_keys=True, default=str)
            hash_key = hashlib.sha256(json_str.encode()).hexdigest()[:16]
            return f"{prefix}:{hash_key}" if prefix else hash_key
        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            # Fallback to timestamp-based key
            return f"{prefix}:nocache:{time.time()}"

    async def search_candidates_by_job(
        self,
        job_data: Dict[str, Any],
        top_k: int = 10,
        min_similarity: float = 0.5,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:

        start_time = time.time()

        # Generate cache key
        if use_cache:
            cache_key_data = {
                "type": "candidates_by_job",
                "title": job_data.get("title", ""),
                "skills": sorted(job_data.get("required_skills", [])),
                "top_k": top_k,
                "min_similarity": min_similarity,
            }
            cache_key = self._generate_cache_key(cache_key_data, "vector_search")

            # Try cache
            try:
                cached_results = await cache_service.get(cache_key)
                if cached_results:
                    elapsed = (time.time() - start_time) * 1000
                    logger.info(f"Vector search cache HIT! (saved ~{elapsed:.2f}ms)")
                    return cached_results
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")

        logger.info("Vector search cache MISS - Searching...")

        try:
            # Generate job embedding
            job_embedding = await self.embedding_service.generate_job_embedding(
                job_data
            )

            # Get ChromaDB collection
            collection = self.chroma_manager.get_or_create_collection(
                "resume_embeddings"
            )

            # Perform vector search
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
                    # Convert distance to similarity, ChromaDB uses L2 distance
                    similarity = 1 / (1 + distance)

                    if similarity >= min_similarity:
                        candidates.append(
                            {
                                "rank": idx + 1,
                                "candidate_id": candidate_id,
                                "similarity_score": round(similarity, 4),
                                "metadata": metadata or {},
                            }
                        )

            elapsed = (time.time() - start_time) * 1000
            logger.info(
                f"Vector search found {len(candidates)} candidates in {elapsed:.2f}ms"
            )

            # Cache results
            if use_cache and candidates:
                try:
                    await cache_service.set(cache_key, candidates, ttl=1800)
                except Exception as e:
                    logger.warning(f"Cache set failed: {e}")

            return candidates

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def search_jobs_by_candidate(
        self,
        candidate_data: Dict[str, Any],
        top_k: int = 50,
        min_similarity: float = 0.5,
        filters: Optional[Dict[str, Any]] = None,
        skip_cache: bool = False,
    ) -> List[Dict[str, Any]]:

        cache_key_data = {
            "candidate_data": candidate_data,
            "top_k": top_k,
            "min_similarity": min_similarity,
            "filters": filters,
        }
        cache_key = self._generate_cache_key(cache_key_data, "vector_search_candidate")

        if not skip_cache:
            try:
                cached_results = await cache_service.get(cache_key)
                if cached_results:
                    logger.info("Vector search cache HIT!")
                    return cached_results
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")

        start_time = time.time()
        logger.info("Vector search cache MISS - Searching...")

        try:
            # Generate resume embedding
            resume_embedding = await self.embedding_service.generate_resume_embedding(
                candidate_data
            )

            # Query ChromaDB
            collection = self.chroma_manager.get_or_create_collection("job_embeddings")

            where = None
            if filters:
                where = self._build_where_clause(filters)

            results = collection.query(
                query_embeddings=[resume_embedding],
                n_results=top_k * 2,
                where=where,
                include=["metadatas", "distances", "documents"],
            )

            # Process results
            jobs = []
            if results and results["ids"]:
                for i, job_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 / (1 + distance)

                    if similarity >= min_similarity:
                        metadata = (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        )

                        jobs.append(
                            {
                                "job_id": job_id,
                                "similarity_score": round(similarity, 4),
                                "metadata": metadata,
                                "rank": len(jobs) + 1,
                            }
                        )

            jobs.sort(key=lambda x: x["similarity_score"], reverse=True)
            jobs = jobs[:top_k]

            search_time = (time.time() - start_time) * 1000

            if not skip_cache:
                try:
                    await cache_service.set(cache_key, jobs, ttl=86400)
                except Exception as e:
                    logger.warning(f"Cache set failed: {e}")

            logger.info(f"Vector search found {len(jobs)} jobs in {search_time:.2f}ms")

            return jobs

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def hybrid_search(
        self,
        query_data: Dict[str, Any],
        search_type: str = "candidates",
        top_k: int = 20,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
        skip_cache: bool = False,
    ) -> List[Dict[str, Any]]:

        cache_key_data = {
            "query_data": query_data,
            "search_type": search_type,
            "top_k": top_k,
            "vector_weight": vector_weight,
            "keyword_weight": keyword_weight,
        }
        cache_key = self._generate_cache_key(cache_key_data, "hybrid_search")

        if not skip_cache:
            try:
                cached_results = await cache_service.get(cache_key)
                if cached_results:
                    logger.info("Hybrid search cache HIT!")
                    return cached_results
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")

        logger.info("Hybrid search cache MISS - Searching...")

        try:
            # Vector search
            if search_type == "candidates":
                vector_results = await self.search_candidates_by_job(
                    query_data, top_k=top_k * 2, min_similarity=0.4, use_cache=False
                )
            else:
                vector_results = await self.search_jobs_by_candidate(
                    query_data, top_k=top_k * 2, min_similarity=0.4, skip_cache=True
                )

            # Keyword matching (using metadata)
            required_skills = set(query_data.get("required_skills", []))

            for result in vector_results:
                metadata = result.get("metadata", {})
                candidate_skills_str = metadata.get("skills", "")

                # Handle skills as string or list
                if isinstance(candidate_skills_str, str):
                    candidate_skills = set(
                        s.strip() for s in candidate_skills_str.split(",") if s.strip()
                    )
                elif isinstance(candidate_skills_str, list):
                    candidate_skills = set(candidate_skills_str)
                else:
                    candidate_skills = set()

                # Calculate keyword overlap
                if required_skills:
                    keyword_score = len(required_skills & candidate_skills) / len(
                        required_skills
                    )
                else:
                    keyword_score = 0.5

                # Combine scores
                vector_score = result["similarity_score"]
                combined_score = (vector_score * vector_weight) + (
                    keyword_score * keyword_weight
                )

                result["keyword_score"] = round(keyword_score, 4)
                result["combined_score"] = round(combined_score, 4)

            # Sort by combined score
            vector_results.sort(key=lambda x: x["combined_score"], reverse=True)
            final_results = vector_results[:top_k]

            # Cache the results
            if not skip_cache:
                try:
                    await cache_service.set(cache_key, final_results, ttl=86400)
                except Exception as e:
                    logger.warning(f"Cache set failed: {e}")

            return final_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def _build_where_clause(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        where = {}

        if "years_experience" in filters:
            exp_filter = filters["years_experience"]
            if "min" in exp_filter:
                where["years_experience"] = {"$gte": exp_filter["min"]}
            if "max" in exp_filter:
                where["years_experience"] = {"$lte": exp_filter["max"]}

        if "location" in filters:
            where["location"] = filters["location"]

        return where if where else None


vector_search_service = VectorSearchService()
