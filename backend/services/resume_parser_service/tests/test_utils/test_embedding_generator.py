"""Tests for embedding generation utilities."""

import pytest
import numpy as np
from app.utils.embedding_generator import (
    generate_resume_embedding,
    calculate_similarity,
)


@pytest.fixture
def sample_resume_dict():
    """Sample resume data for embedding."""
    return {
        "full_name": "John Doe",
        "email": "john@example.com",
        "summary": "Experienced software engineer with Python and FastAPI",
        "skills": {
            "programming_languages": ["Python", "JavaScript"],
            "frameworks": ["FastAPI", "React"],
        },
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Tech Corp",
                "description": "Built scalable APIs",
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "MIT",
            }
        ],
    }


def test_generate_resume_embedding(sample_resume_dict):
    """Test generating resume embedding."""
    embedding = generate_resume_embedding(sample_resume_dict)

    assert embedding is not None
    assert isinstance(embedding, (list, np.ndarray))
    assert len(embedding) == 384  # Default model dimension

    # Check values are floats
    if isinstance(embedding, list):
        assert all(isinstance(x, (float, np.floating)) for x in embedding)


def test_generate_embedding_empty_resume():
    """Test generating embedding from empty resume."""
    empty_resume = {}
    embedding = generate_resume_embedding(empty_resume)

    # Should still generate an embedding
    assert embedding is not None
    assert len(embedding) == 384


def test_generate_embedding_minimal_data():
    """Test generating embedding with minimal data."""
    minimal_resume = {
        "full_name": "Jane Doe",
        "summary": "Software developer",
    }
    embedding = generate_resume_embedding(minimal_resume)

    assert embedding is not None
    assert len(embedding) == 384


def test_calculate_similarity_identical():
    """Test similarity between identical embeddings."""
    embedding1 = [1.0] * 384
    embedding2 = [1.0] * 384

    similarity = calculate_similarity(embedding1, embedding2)

    assert 0.99 <= similarity <= 1.0  # Should be very close to 1


def test_calculate_similarity_different():
    """Test similarity between different embeddings."""
    # Create orthogonal-ish vectors
    embedding1 = [1.0 if i < 192 else 0.0 for i in range(384)]
    embedding2 = [0.0 if i < 192 else 1.0 for i in range(384)]

    similarity = calculate_similarity(embedding1, embedding2)

    assert -1.0 <= similarity <= 1.0
    assert similarity < 0.5  # Should be low similarity


def test_calculate_similarity_range():
    """Test similarity score is in valid range."""
    np.random.seed(42)  # For reproducibility
    embedding1 = np.random.randn(384).tolist()
    embedding2 = np.random.randn(384).tolist()

    similarity = calculate_similarity(embedding1, embedding2)

    assert -1.0 <= similarity <= 1.0


def test_embedding_consistency(sample_resume_dict):
    """Test that same input produces same embedding."""
    embedding1 = generate_resume_embedding(sample_resume_dict)
    embedding2 = generate_resume_embedding(sample_resume_dict)

    # Should be identical or very similar
    similarity = calculate_similarity(embedding1, embedding2)
    assert similarity > 0.99


def test_embedding_with_none_values():
    """Test embedding generation with None values."""
    resume_with_nones = {
        "full_name": "Test User",
        "email": None,
        "summary": None,
        "skills": None,
    }

    embedding = generate_resume_embedding(resume_with_nones)

    assert embedding is not None
    assert len(embedding) == 384


def test_embedding_dimensions():
    """Test that embeddings have correct dimensions."""
    resume = {"full_name": "Test", "summary": "Developer"}
    embedding = generate_resume_embedding(resume)

    assert len(embedding) == 384
    assert all(isinstance(x, (float, np.floating)) for x in embedding)
