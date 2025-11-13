"""Detect duplicate resume uploads."""

import hashlib
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume

logger = logging.getLogger(__name__)


def calculate_file_hash(file_bytes: bytes) -> str:
    """Calculate SHA-256 hash of file content.

    Args:
        file_bytes: File content as bytes

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(file_bytes).hexdigest()


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using character overlap.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    # Convert to lowercase and create character sets
    chars1 = set(text1.lower())
    chars2 = set(text2.lower())

    # Jaccard similarity
    intersection = len(chars1 & chars2)
    union = len(chars1 | chars2)

    return intersection / union if union > 0 else 0.0


async def check_duplicate_by_hash(
    db: AsyncSession, user_id: str, file_hash: str
) -> Optional[Resume]:
    """Check if resume with same file hash exists.

    Args:
        db: Database session
        user_id: User ID
        file_hash: File SHA-256 hash

    Returns:
        Existing resume or None
    """
    result = await db.execute(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.file_hash == file_hash,
            Resume.is_deleted == False,
        )
    )

    return result.scalar_one_or_none()


async def check_duplicate_by_content(
    db: AsyncSession, user_id: str, raw_text: str, threshold: float = 0.90
) -> Optional[Resume]:
    """Check if similar resume content exists.

    Args:
        db: Database session
        user_id: User ID
        raw_text: Resume text content
        threshold: Similarity threshold (0-1)

    Returns:
        Similar resume or None
    """
    # Get all user's resumes with text
    result = await db.execute(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.raw_text.isnot(None),
            Resume.is_deleted == False,
        )
    )

    existing_resumes = result.scalars().all()

    for resume in existing_resumes:
        similarity = calculate_text_similarity(raw_text, resume.raw_text)

        if similarity >= threshold:
            logger.info(f"Found duplicate resume (similarity: {similarity:.2f})")
            return resume

    return None


async def find_all_duplicates(
    db: AsyncSession, user_id: str, resume_id: str
) -> List[Resume]:
    """Find all potential duplicates of a resume.

    Args:
        db: Database session
        user_id: User ID
        resume_id: Resume to check

    Returns:
        List of potential duplicate resumes
    """
    # Get target resume
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )

    target_resume = result.scalar_one_or_none()

    if not target_resume or not target_resume.raw_text:
        return []

    # Check against all other resumes
    duplicates = []

    result = await db.execute(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.id != resume_id,
            Resume.is_deleted == False,
        )
    )

    all_resumes = result.scalars().all()

    for resume in all_resumes:
        if not resume.raw_text:
            continue

        # Check file hash
        if target_resume.file_hash and resume.file_hash == target_resume.file_hash:
            duplicates.append(resume)
            continue

        # Check text similarity
        similarity = calculate_text_similarity(target_resume.raw_text, resume.raw_text)

        if similarity >= 0.85:
            duplicates.append(resume)

    logger.info(f"Found {len(duplicates)} potential duplicates")
    return duplicates
