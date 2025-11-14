from typing import List

from common.logging import get_logger
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = get_logger(__name__)


class EmbeddingService:

    def __init__(self):
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding service initialized with all-MiniLM-L6-v2 model")
        except Exception as e:
            logger.error(f"Error initializing embedding service: {str(e)}")
            raise

    def embed_text(self, text: str) -> List[float]:
        # Convert text to embedding vector (384-dimensional)
        try:
            if not text:
                return [0.0] * 384

            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise

    def embed_job(self, job) -> List[float]:
        # Create embedding for a job
        try:
            # Combine job title, description, and location for context
            text = f"{job.title} {job.description} {job.location} {job.job_type} {job.experience_level}"
            embedding = self.embed_text(text)
            logger.debug(f"Generated embedding for job: {job.id}")
            return embedding
        except Exception as e:
            logger.error(f"Error embedding job: {str(e)}")
            raise

    def embed_query(self, query: str) -> List[float]:
        # Create embedding for search query
        try:
            return self.embed_text(query)
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise

    @staticmethod
    def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        # Calculate cosine similarity between two embeddings (0.0 to 1.0)
        try:
            if not embedding1 or not embedding2:
                return 0.0

            sim = cosine_similarity([embedding1], [embedding2])[0][0]
            return float(sim)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    def find_similar_jobs(
        self,
        query_embedding: List[float],
        jobs: list,
        top_k: int = 10,
        similarity_threshold: float = 0.3,
    ) -> list:
        # Find top-k jobs similar to query embedding
        try:
            similarities = []

            for job in jobs:
                # Use job's embedding or create one
                if hasattr(job, "embedding") and job.embedding:
                    job_embedding = job.embedding
                else:
                    job_embedding = self.embed_job(job)

                # Calculate similarity
                sim = self.calculate_similarity(query_embedding, job_embedding)

                # Only include jobs above threshold
                if sim >= similarity_threshold:
                    similarities.append((job, sim))

            # Sort by similarity (highest first)
            sorted_results = sorted(similarities, key=lambda x: x[1], reverse=True)

            logger.debug(
                f"Found {len(sorted_results)} similar jobs (threshold: {similarity_threshold})"
            )
            return sorted_results[:top_k]

        except Exception as e:
            logger.error(f"Error finding similar jobs: {str(e)}")
            return []


embedding_service = EmbeddingService()
