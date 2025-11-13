"""Celery tasks for resume parsing - FIXED FOR MULTIPROCESSING."""

import logging
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.resume import Resume
from app.utils.file_parser import parse_file
from app.utils.embedding_generator import generate_resume_embedding

logger = logging.getLogger(__name__)

# ✅ CREATE SYNC DATABASE SESSION FOR CELERY
sync_database_url = settings.database_url_resume.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)

sync_engine = create_engine(sync_database_url, echo=False)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


@celery_app.task(name="parse_resume_async", bind=True, max_retries=3)
def parse_resume_async(self, resume_id: str):
    """Parse a resume asynchronously."""
    logger.info(f"🔄 [Task {self.request.id}] Parsing resume: {resume_id}")

    db = SessionLocal()

    try:
        # Get resume from database
        result = db.execute(select(Resume).where(Resume.id == uuid.UUID(resume_id)))
        resume = result.scalar_one_or_none()

        if not resume:
            logger.error(f"❌ Resume not found: {resume_id}")
            return {"status": "error", "error": "Resume not found"}

        # ✅ FIXED: Get file path (database already has "uploads/" prefix)
        base_dir = Path(__file__).resolve().parent.parent.parent
        file_path = base_dir / resume.file_path  # ← No "uploads/" added here!

        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return {"status": "error", "error": "File not found"}

        # Parse file
        logger.info(f"📄 Parsing file: {file_path}")
        raw_text = parse_file(file_path, resume.file_type)

        # Import and call extract_resume_data INSIDE task
        from app.utils.nlp_processor import extract_resume_data

        # Extract data using NLP
        logger.info(f"🧠 Extracting resume data...")
        resume_data = extract_resume_data(raw_text)

        # Generate embedding
        logger.info(f"🔢 Generating embedding...")
        embedding = generate_resume_embedding(resume_data)

        # Update resume
        resume.raw_text = raw_text
        resume.parsed_text = raw_text
        resume.full_name = resume_data.get("full_name")
        resume.email = resume_data.get("email")
        resume.phone = resume_data.get("phone")
        resume.location = resume_data.get("location")
        resume.skills = resume_data.get("skills")
        resume.experience = resume_data.get("experience")
        resume.education = resume_data.get("education")
        resume.certifications = resume_data.get("certifications")
        resume.total_experience_years = resume_data.get("total_experience_years", 0)
        resume.embedding = embedding
        resume.embedding_model = "all-MiniLM-L6-v2"
        resume.is_parsed = True
        resume.is_embedding_generated = True
        resume.parsing_version = "2.0.0"

        db.commit()

        logger.info(
            f"✅ [Task {self.request.id}] Resume parsed successfully: {resume_id}"
        )

        return {
            "status": "success",
            "resume_id": resume_id,
            "full_name": resume.full_name,
            "skills_count": len(resume.skills) if resume.skills else 0,
        }

    except Exception as e:
        logger.error(
            f"❌ [Task {self.request.id}] Error parsing resume: {str(e)}", exc_info=True
        )
        db.rollback()

        # Retry task
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(name="batch_parse_resumes_async")
def batch_parse_resumes_async(resume_ids: list[str]):
    """Parse multiple resumes asynchronously.

    Args:
        resume_ids: List of resume UUIDs to parse

    Returns:
        dict: Batch parsing result
    """
    logger.info(f"📦 Batch parsing {len(resume_ids)} resumes...")

    # Queue individual tasks
    tasks = []
    for resume_id in resume_ids:
        task = parse_resume_async.delay(resume_id)
        tasks.append(task.id)

    return {
        "status": "queued",
        "total_resumes": len(resume_ids),
        "task_ids": tasks,
    }
