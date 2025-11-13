"""Resume service for parsing and managing resumes."""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeParsed, ResumeUpdate
from app.utils.file_parser import parse_file
from app.utils.nlp_processor import (
    calculate_experience_years,
    extract_education,
    extract_email,
    extract_experience,
    extract_location,
    extract_name,
    extract_phone,
    extract_summary,
)
from app.utils.skill_extractor import extract_skills
from app.core.websocket import ws_manager

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume operations."""

    def __init__(self, db: AsyncSession):
        """Initialize resume service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_resume(self, resume_data: ResumeCreate) -> Resume:
        """Create a new resume entry.

        Args:
            resume_data: Resume creation data

        Returns:
            Created resume
        """
        resume = Resume(
            id=uuid.uuid4(),
            user_id=resume_data.user_id,
            filename=resume_data.filename,
            file_path=resume_data.file_path,
            file_size=resume_data.file_size,
            file_type=resume_data.file_type,
            is_parsed=False,
            is_embedding_generated=False,
        )

        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        logger.info(f"Created resume: {resume.id}")
        return resume

    async def get_resume_by_id(self, resume_id: uuid.UUID) -> Optional[Resume]:
        """Get resume by ID."""
        result = await self.db.execute(
            select(Resume).where(
                Resume.id == resume_id, Resume.is_deleted == False  # ← CHANGED
            )
        )
        return result.scalar_one_or_none()

    async def get_resumes_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 10
    ) -> list[Resume]:
        """Get resumes for a user."""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.is_deleted == False)  # ← CHANGED
            .offset(skip)
            .limit(limit)
            .order_by(Resume.created_at.desc())
        )
        return list(result.scalars().all())

    async def parse_resume(
        self, resume_id: uuid.UUID, use_ocr: bool = False
    ) -> ResumeParsed:
        """
        Parse resume with WebSocket progress updates.

        Stages: extraction -> nlp -> skills -> experience -> embedding -> ai_summary -> complete
        """
        resume = await self.get_resume_by_id(resume_id)

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        user_id = str(resume.user_id)

        try:
            logger.info(f"🔄 Parsing resume: {resume.id} ({resume.filename})")

            # Stage 1: Text extraction (10%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="extraction",
                progress=10,
                message="📄 Extracting text from PDF...",
            )

            base_dir = Path(__file__).resolve().parent.parent.parent
            full_path = base_dir / "uploads" / resume.file_path

            raw_text = parse_file(full_path, use_ocr=use_ocr)

            if not raw_text:
                raise ValueError("No text extracted from resume")

            logger.info(f"✅ Extracted {len(raw_text)} characters")

            from app.utils.file_hash import calculate_file_hash

            file_hash = calculate_file_hash(full_path)

            # Stage 2: Extract basic info (30%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="nlp",
                progress=30,
                message="🧠 Extracting contact information...",
            )

            name = extract_name(raw_text)
            email = extract_email(raw_text)
            phone = extract_phone(raw_text)
            location = extract_location(raw_text)

            # Stage 3: Extract skills (50%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="skills",
                progress=50,
                message="⚙️ Extracting technical skills...",
            )

            skills = extract_skills(raw_text)

            # Stage 4: Extract experience and education (65%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="experience",
                progress=65,
                message="💼 Extracting work experience...",
            )

            from app.utils.experience_extractor import (
                extract_experiences,
                calculate_total_experience_years,
            )

            experience = extract_experiences(raw_text)
            total_years = calculate_total_experience_years(experience)

            education = extract_education(raw_text)

            # Stage 5: Generate embeddings (80%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="embedding",
                progress=80,
                message="🔢 Generating vector embeddings...",
            )

            from app.utils.embedding_generator import generate_resume_embedding

            resume_data = {
                "full_name": name,
                "email": email,
                "phone": phone,
                "location": location,
                "skills": skills,
                "experience": experience,
                "education": education,
                "total_experience_years": total_years,
            }
            embedding = generate_resume_embedding(resume_data)

            # Stage 6: Generate AI summary (92%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="ai_summary",
                progress=92,
                message="🤖 Generating AI professional summary...",
            )

            from app.utils.ai_summary_generator import generate_professional_summary

            ai_summary = generate_professional_summary(resume_data)

            # Stage 7: Save data to DB (98%)
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="saving",
                progress=98,
                message="💾 Saving parsed data...",
            )

            resume.raw_text = raw_text
            resume.parsed_text = raw_text
            resume.full_name = name
            resume.email = email
            resume.phone = phone
            resume.location = location
            resume.total_experience_years = total_years
            resume.skills = skills
            resume.experience = {"entries": experience}
            resume.education = {"entries": education}
            resume.embedding = embedding
            resume.is_embedding_generated = True
            resume.ai_generated_summary = ai_summary
            resume.file_hash = file_hash
            resume.is_parsed = True
            resume.last_parsed_at = datetime.now(timezone.utc)
            resume.parsing_version = "2.0.0"

            await self.db.commit()
            await self.db.refresh(resume)

            # Complete: Send 100% progress and success
            await ws_manager.emit_parsing_progress(
                user_id,
                resume_id,
                resume.filename,
                stage="complete",
                progress=100,
                message="✅ Parsing completed successfully!",
            )

            await ws_manager.emit_parsing_complete(
                user_id, resume_id, resume.filename, success=True
            )

            logger.info(f"✅ Successfully parsed resume: {resume.id}")

            return ResumeParsed(
                raw_text=raw_text,
                parsed_text=raw_text,
                full_name=name,
                email=email,
                phone=phone,
                location=location,
                summary=ai_summary,
                skills=skills,
                experience=experience,
                education=education,
                total_experience_years=total_years,
            )

        except Exception as e:
            logger.error(f"❌ Error parsing resume {resume.id}: {str(e)}")

            await ws_manager.emit_parsing_complete(
                user_id, resume_id, resume.filename, success=False, error=str(e)
            )

            resume.parsing_error = str(e)
            await self.db.commit()

            raise

    async def update_resume(
        self, resume_id: uuid.UUID, update_data: ResumeUpdate
    ) -> Resume:
        """Update resume information.

        Args:
            resume_id: Resume ID
            update_data: Update data

        Returns:
            Updated resume

        Raises:
            ValueError: If resume not found
        """
        resume = await self.get_resume_by_id(resume_id)

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            if hasattr(resume, key):
                setattr(resume, key, value)

        await self.db.commit()
        await self.db.refresh(resume)

        logger.info(f"Updated resume: {resume.id}")
        return resume

    async def delete_resume(
        self, resume_id: uuid.UUID, hard_delete: bool = False
    ) -> bool:
        """Delete resume (soft or hard delete).

        Args:
            resume_id: Resume ID
            hard_delete: Whether to permanently delete

        Returns:
            True if deleted

        Raises:
            ValueError: If resume not found
        """
        resume = await self.get_resume_by_id(resume_id)

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        if hard_delete:
            # Permanent delete
            await self.db.delete(resume)
            logger.info(f"Hard deleted resume: {resume.id}")
        else:
            # Soft delete
            resume.is_deleted = True
            resume.deleted_at = datetime.now(timezone.utc)
            logger.info(f"Soft deleted resume: {resume.id}")

        await self.db.commit()
        return True

    async def count_resumes(self, user_id: Optional[uuid.UUID] = None) -> int:
        """Count resumes."""
        query = select(Resume).where(Resume.is_deleted == False)  # ← CHANGED

        if user_id:
            query = query.where(Resume.user_id == user_id)

        result = await self.db.execute(query)
        return len(list(result.scalars().all()))
