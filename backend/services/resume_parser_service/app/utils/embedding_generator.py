import logging
import os
import threading
import time
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Thread safe model cache
_embedding_model: Optional[SentenceTransformer] = None
_model_lock = threading.Lock()
_model_load_time: Optional[float] = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model, _model_load_time

    if _embedding_model is not None:
        return _embedding_model

    # Thread safe loading
    with _model_lock:
        if _embedding_model is not None:
            return _embedding_model

        logger.info(f"Loading embedding model: {settings.sentence_transformer_model}")
        start_time = time.time()

        try:
            _embedding_model = SentenceTransformer(
                settings.sentence_transformer_model,
                cache_folder="./model_cache",
            )
            _model_load_time = time.time() - start_time

            logger.info(
                f"Embedding model loaded successfully in {_model_load_time:.2f}s"
            )
            logger.info(f"Model memory: ~{_get_model_size_mb(_embedding_model):.0f}MB")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    return _embedding_model


def _get_model_size_mb(model: SentenceTransformer) -> float:
    try:
        total_params = sum(p.numel() for p in model.parameters())
        # Assume float32 (4 bytes per param)
        size_mb = (total_params * 4) / (1024 * 1024)
        return size_mb
    except Exception:
        return 0.0


def preload_model():
    logger.info("Preloading embedding model at startup...")
    get_embedding_model()
    logger.info("Model preloaded and cached")


def get_cache_info() -> dict:
    return {
        "is_cached": _embedding_model is not None,
        "model_name": settings.sentence_transformer_model,
        "load_time": _model_load_time,
        "estimated_memory_mb": (
            _get_model_size_mb(_embedding_model) if _embedding_model else 0
        ),
    }


def generate_resume_embedding(resume_data: dict) -> List[float]:
    try:
        text_parts = []

        # Add name
        if resume_data.get("full_name"):
            text_parts.append(f"Name: {resume_data['full_name']}")

        # Add skills (categorized dict)
        if resume_data.get("skills"):
            if isinstance(resume_data["skills"], dict):
                # Flatten categorized skills
                all_skills = []
                for category_skills in resume_data["skills"].values():
                    if isinstance(category_skills, list):
                        all_skills.extend(category_skills[:10])  # Max 10 per category
                skills_text = ", ".join(all_skills[:50])  # Max 50 total
            elif isinstance(resume_data["skills"], list):
                skills_text = ", ".join(resume_data["skills"][:50])
            else:
                skills_text = ""

            if skills_text:
                text_parts.append(f"Skills: {skills_text}")

        # Add experience (list of dicts)
        if resume_data.get("experience"):
            experience = resume_data["experience"]
            if isinstance(experience, list):
                exp_titles = []
                for exp in experience[:5]:  # Top 5 jobs
                    if isinstance(exp, dict):
                        title = exp.get("title", "")
                        company = exp.get("company", "")
                        if title and company:
                            exp_titles.append(f"{title} at {company}")
                if exp_titles:
                    text_parts.append(f"Experience: {', '.join(exp_titles)}")

        # Add education (list of dicts)
        if resume_data.get("education"):
            education = resume_data["education"]
            if isinstance(education, list):
                edu_degrees = []
                for edu in education[:3]:  # Top 3 degrees
                    if isinstance(edu, dict):
                        degree = edu.get("degree", "")
                        institution = edu.get("institution", "")
                        if degree and institution:
                            edu_degrees.append(f"{degree} from {institution}")
                if edu_degrees:
                    text_parts.append(f"Education: {', '.join(edu_degrees)}")

        # Add years of experience
        if resume_data.get("total_experience_years"):
            years = resume_data["total_experience_years"]
            text_parts.append(f"Experience: {years} years")

        # Combine all text
        combined_text = " | ".join(filter(None, text_parts))

        if not combined_text:
            logger.warning("No text available for embedding generation")
            return [0.0] * settings.embedding_dimension

        # Use cached model
        model = get_embedding_model()

        # Generate embedding
        start_time = time.time()
        embedding = model.encode(combined_text, show_progress_bar=False)
        encode_time = time.time() - start_time

        # Convert to list
        embedding_list = embedding.tolist()

        if len(embedding_list) != settings.embedding_dimension:
            logger.error(
                f"Embedding dimension mismatch: {len(embedding_list)} != {settings.embedding_dimension}"
            )
            return [0.0] * settings.embedding_dimension

        logger.info(
            f"Generated embedding of dimension {len(embedding_list)} "
            f"in {encode_time:.3f}s"
        )
        return embedding_list

    except Exception as e:
        logger.error(f"Error generating embedding: {e}", exc_info=True)
        return [0.0] * settings.embedding_dimension


def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Ensure result is between 0 and 1
        similarity = max(0.0, min(1.0, float(similarity)))

        return similarity

    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0


def search_similar_resumes(
    query_embedding: List[float],
    resume_embeddings: List[tuple[str, List[float]]],
    top_k: int = 10,
    min_score: float = 0.5,
) -> List[tuple[str, float]]:
    similarities = []

    for resume_id, embedding in resume_embeddings:
        score = calculate_similarity(query_embedding, embedding)
        if score >= min_score:
            similarities.append((resume_id, score))

    # Sort by score descending
    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities[:top_k]
