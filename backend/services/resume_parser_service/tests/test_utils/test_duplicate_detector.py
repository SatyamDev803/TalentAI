import pytest
from uuid import uuid4

from app.utils.duplicate_detector import (
    calculate_text_similarity,
    check_duplicate_by_hash,
    check_duplicate_by_content,
    find_all_duplicates,
)
from app.models.resume import Resume


class TestTextSimilarity:

    def test_identical_texts(self):
        text1 = "This is a software engineer resume"
        text2 = "This is a software engineer resume"

        similarity = calculate_text_similarity(text1, text2)

        assert similarity == 1.0

    def test_completely_different_texts(self):
        text1 = "Python developer with Django experience"
        text2 = "Marketing manager skilled in SEO"

        similarity = calculate_text_similarity(text1, text2)

        assert similarity < 0.3

    def test_similar_texts(self):
        text1 = "Software engineer with 5 years Python experience"
        text2 = "Software engineer with 3 years Python experience"

        similarity = calculate_text_similarity(text1, text2)

        assert 0.7 < similarity < 1.0

    def test_empty_texts(self):
        assert calculate_text_similarity("", "text") == 0.0
        assert calculate_text_similarity("text", "") == 0.0
        assert calculate_text_similarity("", "") == 0.0

    def test_case_insensitive(self):
        text1 = "Python Developer"
        text2 = "python developer"

        similarity = calculate_text_similarity(text1, text2)

        assert similarity == 1.0

    def test_word_level_similarity(self):
        # Single words should have 100% overlap
        text1 = "hello"
        text2 = "hello"

        similarity = calculate_text_similarity(text1, text2)

        assert similarity == 1.0

        # Different single words should have 0% overlap
        text3 = "hello"
        text4 = "world"

        similarity2 = calculate_text_similarity(text3, text4)

        assert similarity2 == 0.0


@pytest.mark.asyncio
class TestCheckDuplicateByHash:

    async def test_no_duplicate_found(self, db_session):
        user_id = uuid4()
        file_hash = "abc123def456"

        result = await check_duplicate_by_hash(db_session, user_id, file_hash)

        assert result is None

    async def test_duplicate_found(self, db_session):
        user_id = uuid4()
        file_hash = "abc123def456"

        # Create existing resume (matching your model exactly)
        existing_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash=file_hash,
            raw_text="Sample text",
            is_deleted=False,
        )
        db_session.add(existing_resume)
        await db_session.commit()
        await db_session.refresh(existing_resume)

        # Check for duplicate
        result = await check_duplicate_by_hash(db_session, user_id, file_hash)

        assert result is not None
        assert result.user_id == user_id
        assert result.file_hash == file_hash

    async def test_ignores_deleted_resumes(self, db_session):
        user_id = uuid4()
        file_hash = "abc123def456"

        # Create deleted resume
        deleted_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash=file_hash,
            raw_text="Sample text",
            is_deleted=True,  # Deleted
        )
        db_session.add(deleted_resume)
        await db_session.commit()

        # Check for duplicate
        result = await check_duplicate_by_hash(db_session, user_id, file_hash)

        assert result is None

    async def test_ignores_other_users_resumes(self, db_session):
        user1_id = uuid4()
        user2_id = uuid4()
        file_hash = "abc123def456"

        # Create resume for user1
        user1_resume = Resume(
            user_id=user1_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash=file_hash,
            raw_text="Sample text",
            is_deleted=False,
        )
        db_session.add(user1_resume)
        await db_session.commit()

        # Check for duplicate for user2
        result = await check_duplicate_by_hash(db_session, user2_id, file_hash)

        assert result is None


@pytest.mark.asyncio
class TestCheckDuplicateByContent:

    async def test_no_duplicate_found(self, db_session):
        user_id = uuid4()
        raw_text = "Software engineer with Python experience"

        result = await check_duplicate_by_content(db_session, user_id, raw_text)

        assert result is None

    async def test_duplicate_found_high_similarity(self, db_session):
        user_id = uuid4()

        # Create existing resume
        existing_text = "Software engineer with 5 years Python experience"
        existing_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash1",
            raw_text=existing_text,
            is_deleted=False,
        )
        db_session.add(existing_resume)
        await db_session.commit()
        await db_session.refresh(existing_resume)

        # Check for duplicate with similar text
        similar_text = "Software engineer with 5 years Python experience"
        result = await check_duplicate_by_content(
            db_session, user_id, similar_text, threshold=0.90
        )

        assert result is not None
        assert result.user_id == user_id

    async def test_no_duplicate_low_similarity(self, db_session):
        user_id = uuid4()

        # Create existing resume
        existing_text = "Software engineer with Python experience"
        existing_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash1",
            raw_text=existing_text,
            is_deleted=False,
        )
        db_session.add(existing_resume)
        await db_session.commit()

        # Check for duplicate with different text
        different_text = "Marketing manager with SEO skills"
        result = await check_duplicate_by_content(
            db_session, user_id, different_text, threshold=0.90
        )

        assert result is None

    async def test_empty_text_returns_none(self, db_session):
        user_id = uuid4()

        result = await check_duplicate_by_content(
            db_session, user_id, "", threshold=0.90
        )

        assert result is None


@pytest.mark.asyncio
class TestFindAllDuplicates:

    async def test_no_duplicates_found(self, db_session):
        user_id = uuid4()

        # Create target resume
        target_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash1",
            raw_text="Software engineer with Python",
            is_deleted=False,
        )
        db_session.add(target_resume)
        await db_session.commit()
        await db_session.refresh(target_resume)

        # Find duplicates
        duplicates = await find_all_duplicates(db_session, user_id, target_resume.id)

        assert len(duplicates) == 0

    async def test_finds_duplicate_by_hash(self, db_session):
        user_id = uuid4()
        file_hash = "same_hash_123"

        # Create target resume
        target_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash=file_hash,
            raw_text="Software engineer",
            is_deleted=False,
        )

        # Create duplicate by hash
        duplicate_resume = Resume(
            user_id=user_id,
            filename="resume2.pdf",
            file_path="/tmp/resume2.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash=file_hash,  # Same hash
            raw_text="Different text",
            is_deleted=False,
        )

        db_session.add(target_resume)
        db_session.add(duplicate_resume)
        await db_session.commit()
        await db_session.refresh(target_resume)
        await db_session.refresh(duplicate_resume)

        # Find duplicates
        duplicates = await find_all_duplicates(db_session, user_id, target_resume.id)

        assert len(duplicates) == 1
        assert duplicates[0].id == duplicate_resume.id

    async def test_finds_duplicate_by_content(self, db_session):
        user_id = uuid4()

        # Create target resume
        target_text = "Software engineer with 5 years Python experience"
        target_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash1",
            raw_text=target_text,
            is_deleted=False,
        )

        # Create similar resume
        similar_text = "Software engineer with 5 years Python experience"
        similar_resume = Resume(
            user_id=user_id,
            filename="resume2.pdf",
            file_path="/tmp/resume2.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash2",
            raw_text=similar_text,
            is_deleted=False,
        )

        db_session.add(target_resume)
        db_session.add(similar_resume)
        await db_session.commit()
        await db_session.refresh(target_resume)
        await db_session.refresh(similar_resume)

        # Find duplicates
        duplicates = await find_all_duplicates(db_session, user_id, target_resume.id)

        assert len(duplicates) == 1
        assert duplicates[0].id == similar_resume.id

    async def test_finds_multiple_duplicates(self, db_session):
        user_id = uuid4()

        # Create target resume
        target_resume = Resume(
            user_id=user_id,
            filename="resume1.pdf",
            file_path="/tmp/resume1.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash1",
            raw_text="Software engineer with Python",
            is_deleted=False,
        )

        # Create duplicate 1 (by hash)
        duplicate1 = Resume(
            user_id=user_id,
            filename="resume2.pdf",
            file_path="/tmp/resume2.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash1",  # Same hash
            raw_text="Different text",
            is_deleted=False,
        )

        # Create duplicate 2 (by content)
        duplicate2 = Resume(
            user_id=user_id,
            filename="resume3.pdf",
            file_path="/tmp/resume3.pdf",
            file_size=1024,
            file_type="pdf",
            file_hash="hash2",
            raw_text="Software engineer with Python",  # Same text
            is_deleted=False,
        )

        db_session.add_all([target_resume, duplicate1, duplicate2])
        await db_session.commit()
        await db_session.refresh(target_resume)
        await db_session.refresh(duplicate1)
        await db_session.refresh(duplicate2)

        # Find duplicates
        duplicates = await find_all_duplicates(db_session, user_id, target_resume.id)

        assert len(duplicates) == 2

    async def test_resume_not_found(self, db_session):
        user_id = uuid4()
        fake_resume_id = uuid4()

        duplicates = await find_all_duplicates(db_session, user_id, fake_resume_id)

        assert len(duplicates) == 0
