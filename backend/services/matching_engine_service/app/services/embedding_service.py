import asyncio
from typing import List, Dict, Any
import hashlib
from sentence_transformers import SentenceTransformer
import numpy as np

from common.logging import get_logger
from app.core.cache import cache_service

logger = get_logger(__name__)


class EmbeddingService:

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):

        self.model_name = model_name
        self.model = None
        self._dimension = 384
        self._model_loading = False

    async def _load_model(self):

        if self.model is not None:
            return

        # Prevent concurrent model loading
        if self._model_loading:
            while self._model_loading:
                await asyncio.sleep(0.1)
            return

        try:
            self._model_loading = True
            logger.info(f"Loading embedding model: {self.model_name}")

            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, SentenceTransformer, self.model_name
            )

            self._dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded: {self.model_name} (dim: {self._dimension})")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise
        finally:
            self._model_loading = False

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_cache_key(self, text: str) -> str:
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
        return f"embedding:{text_hash}"

    async def generate_embedding(
        self, text: str, use_cache: bool = True
    ) -> List[float]:

        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self._dimension

        if use_cache:
            cache_key = self._generate_cache_key(text)
            cached_embedding = await cache_service.get(cache_key)

            if cached_embedding:
                logger.debug(f"Embedding cache HIT ({len(text)} chars)")
                return cached_embedding

        logger.debug(f"Embedding cache MISS - Generating ({len(text)} chars)")

        try:
            await self._load_model()

            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, lambda: self.model.encode(text, convert_to_numpy=True)
            )
            embedding_list = embedding.tolist()

            if use_cache:
                cache_key = self._generate_cache_key(text)
                await cache_service.set(cache_key, embedding_list, ttl=604800)
                logger.debug("Embedding cached (7 days)")

            return embedding_list

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * self._dimension

    async def generate_embeddings_batch(
        self, texts: List[str], use_cache: bool = True
    ) -> List[List[float]]:
        if not texts:
            return []

        results = []
        uncached_indices = []
        uncached_texts = []

        for idx, text in enumerate(texts):
            if use_cache:
                cache_key = self._generate_cache_key(text)
                cached = await cache_service.get(cache_key)

                if cached:
                    results.append(cached)
                    logger.debug(f"Batch embedding cache HIT [{idx}]")
                else:
                    results.append(None)
                    uncached_indices.append(idx)
                    uncached_texts.append(text)
            else:
                results.append(None)
                uncached_indices.append(idx)
                uncached_texts.append(text)

        if uncached_texts:
            logger.info(
                f"Generating {len(uncached_texts)}/{len(texts)} uncached embeddings"
            )

            try:
                await self._load_model()

                loop = asyncio.get_event_loop()
                new_embeddings = await loop.run_in_executor(
                    None,
                    lambda: self.model.encode(
                        uncached_texts,
                        convert_to_numpy=True,
                        show_progress_bar=len(uncached_texts) > 10,
                    ),
                )
                new_embeddings_list = new_embeddings.tolist()

                for idx, embedding in zip(uncached_indices, new_embeddings_list):
                    results[idx] = embedding

                    if use_cache:
                        cache_key = self._generate_cache_key(texts[idx])
                        await cache_service.set(cache_key, embedding, ttl=604800)

                logger.info(f"Generated and cached {len(uncached_texts)} embeddings")

            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                for idx in uncached_indices:
                    results[idx] = [0.0] * self._dimension

        return results

    def compute_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    async def generate_job_embedding(
        self, job_data: Dict[str, Any], use_cache: bool = True
    ) -> List[float]:

        text_parts = []

        if job_data.get("title"):
            text_parts.append(f"Job Title: {job_data['title']}")

        if job_data.get("description"):
            text_parts.append(f"Description: {job_data['description']}")

        if job_data.get("required_skills"):
            skills = (
                ", ".join(job_data["required_skills"])
                if isinstance(job_data["required_skills"], list)
                else job_data["required_skills"]
            )
            text_parts.append(f"Required Skills: {skills}")

        if job_data.get("experience_level"):
            text_parts.append(f"Experience: {job_data['experience_level']}")

        if job_data.get("location"):
            text_parts.append(f"Location: {job_data['location']}")

        combined_text = " | ".join(text_parts)
        return await self.generate_embedding(combined_text, use_cache=use_cache)

    async def generate_resume_embedding(
        self, resume_data: Dict[str, Any], use_cache: bool = True
    ) -> List[float]:

        text_parts = []

        if resume_data.get("professional_summary"):
            text_parts.append(f"Summary: {resume_data['professional_summary']}")

        if resume_data.get("skills"):
            skills = (
                ", ".join(resume_data["skills"])
                if isinstance(resume_data["skills"], list)
                else resume_data["skills"]
            )
            text_parts.append(f"Skills: {skills}")

        if resume_data.get("experience"):
            text_parts.append(f"Experience: {resume_data['experience']}")

        if resume_data.get("education"):
            text_parts.append(f"Education: {resume_data['education']}")

        combined_text = " | ".join(text_parts)
        return await self.generate_embedding(combined_text, use_cache=use_cache)


embedding_service = EmbeddingService()
