import sys
import asyncio
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

shared_root = project_root.parent.parent.parent / "shared"
sys.path.insert(0, str(shared_root))

from app.services.embedding_service import embedding_service


async def test_embeddings():
    print("Testing Embedding Service\n")

    # Test job embedding
    job_data = {
        "title": "Senior Python Engineer",
        "description": "Build scalable microservices",
        "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "experience_level": "5+ years",
        "location": "Remote",
    }

    print("Generating job embedding...")
    job_embedding = await embedding_service.generate_job_embedding(job_data)
    print(f"   Generated embedding: dimension={len(job_embedding)}")
    print(f"   Sample values: {job_embedding[:5]}\n")

    # Test resume embedding
    resume_data = {
        "professional_summary": "Experienced Python developer specializing in backend systems",
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis"],
        "experience": "6 years in software development",
        "education": "BS Computer Science",
    }

    print("Generating resume embedding...")
    resume_embedding = await embedding_service.generate_resume_embedding(resume_data)
    print(f"   Generated embedding: dimension={len(resume_embedding)}")
    print(f"   Sample values: {resume_embedding[:5]}\n")

    # Test similarity
    print("Computing similarity...")
    similarity = embedding_service.compute_similarity(job_embedding, resume_embedding)
    print(f"   Similarity score: {similarity:.4f} (0-1 scale)")
    print(
        f"   Match quality: {'Excellent' if similarity > 0.8 else 'Good' if similarity > 0.6 else 'Moderate'}\n"
    )


if __name__ == "__main__":
    asyncio.run(test_embeddings())
