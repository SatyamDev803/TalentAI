from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from common.logging import get_logger

logger = get_logger(__name__)


def calculate_text_similarity(text1: str, text2: str) -> float:

    if not text1 or not text2:
        return 0.0

    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Jaccard similarity: intersection / union
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


async def check_duplicate_by_hash(
    db: AsyncSession, user_id: UUID, file_hash: str
) -> Optional[Resume]:

    result = await db.execute(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.file_hash == file_hash,
            Resume.is_deleted.is_(False),
        )
    )

    return result.scalar_one_or_none()


async def check_duplicate_by_content(
    db: AsyncSession, user_id: UUID, raw_text: str, threshold: float = 0.90
) -> Optional[Resume]:

    if not raw_text or not raw_text.strip():
        return None

    # Get all user's resumes with text
    result = await db.execute(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.raw_text.isnot(None),
            Resume.is_deleted.is_(False),
        )
    )

    existing_resumes = result.scalars().all()

    # Compare with each existing resume
    for resume in existing_resumes:
        if not resume.raw_text:
            continue

        similarity = calculate_text_similarity(raw_text, resume.raw_text)

        if similarity >= threshold:
            logger.info(
                f"Found duplicate resume for user {user_id} "
                f"(similarity: {similarity:.2%})"
            )
            return resume

    return None


async def find_all_duplicates(
    db: AsyncSession, user_id: UUID, resume_id: UUID
) -> List[Resume]:

    # Get target resume
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )

    target_resume = result.scalar_one_or_none()

    if not target_resume:
        logger.warning(f"Resume {resume_id} not found")
        return []

    if not target_resume.raw_text:
        logger.warning(f"Resume {resume_id} has no text content")
        return []

    # Get all other resumes for this user
    result = await db.execute(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.id != resume_id,
            Resume.is_deleted.is_(False),
        )
    )

    all_resumes = result.scalars().all()
    duplicates = []

    # Check each resume for duplicates
    for resume in all_resumes:
        is_duplicate = False

        # Check 1: Identical file hash (exact copy)
        if (
            target_resume.file_hash
            and resume.file_hash
            and target_resume.file_hash == resume.file_hash
        ):
            is_duplicate = True
            logger.info(f"Found duplicate by hash: {resume.id}")

        # Check 2: Similar text content
        elif resume.raw_text:
            similarity = calculate_text_similarity(
                target_resume.raw_text, resume.raw_text
            )

            if similarity >= 0.85:
                is_duplicate = True
                logger.info(
                    f"Found duplicate by content: {resume.id} "
                    f"(similarity: {similarity:.2%})"
                )

        if is_duplicate:
            duplicates.append(resume)

    logger.info(
        f"Found {len(duplicates)} potential duplicates " f"for resume {resume_id}"
    )

    return duplicates
