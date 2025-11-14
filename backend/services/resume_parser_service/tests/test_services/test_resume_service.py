import uuid
import pytest
from app.schemas.resume import ResumeCreate
from app.services.resume_service import ResumeService


@pytest.fixture
async def resume_service(db_session):
    return ResumeService(db_session)


@pytest.fixture
def sample_resume_data(test_user_id):
    return ResumeCreate(
        user_id=test_user_id,
        filename="test_resume.pdf",
        file_path="/uploads/test_resume.pdf",
        file_size=12345,
        file_type="pdf",
    )


@pytest.mark.asyncio
async def test_create_resume(resume_service, sample_resume_data):
    resume = await resume_service.create_resume(sample_resume_data)

    assert resume.id is not None
    assert resume.user_id == sample_resume_data.user_id
    assert resume.filename == sample_resume_data.filename
    assert resume.file_path == sample_resume_data.file_path
    assert resume.is_parsed is False
    assert resume.is_embedding_generated is False


@pytest.mark.asyncio
async def test_get_resume_by_id(resume_service, sample_resume_data):
    # Create resume
    created_resume = await resume_service.create_resume(sample_resume_data)

    # Get resume
    resume = await resume_service.get_resume_by_id(created_resume.id)

    assert resume is not None
    assert resume.id == created_resume.id
    assert resume.filename == sample_resume_data.filename


@pytest.mark.asyncio
async def test_get_resume_by_id_not_found(resume_service):
    resume = await resume_service.get_resume_by_id(uuid.uuid4())
    assert resume is None


@pytest.mark.asyncio
async def test_get_resumes_by_user(resume_service, sample_resume_data, test_user_id):
    # Create multiple resumes
    await resume_service.create_resume(sample_resume_data)
    await resume_service.create_resume(
        ResumeCreate(
            user_id=test_user_id,
            filename="resume2.pdf",
            file_path="/uploads/resume2.pdf",
            file_size=54321,
            file_type="pdf",
        )
    )

    # Get resumes
    resumes = await resume_service.get_resumes_by_user(test_user_id, skip=0, limit=10)

    assert len(resumes) == 2
    assert all(r.user_id == test_user_id for r in resumes)


@pytest.mark.asyncio
async def test_count_resumes(resume_service, sample_resume_data, test_user_id):
    # Initially 0
    count = await resume_service.count_resumes(test_user_id)
    assert count == 0

    # Create resume
    await resume_service.create_resume(sample_resume_data)

    # Now 1
    count = await resume_service.count_resumes(test_user_id)
    assert count == 1


@pytest.mark.asyncio
async def test_delete_resume_soft(resume_service, sample_resume_data):
    # Create resume
    resume = await resume_service.create_resume(sample_resume_data)

    # Soft delete
    await resume_service.delete_resume(resume.id, hard_delete=False)

    # Should still exist but marked as deleted
    deleted_resume = await resume_service.get_resume_by_id(resume.id)
    assert deleted_resume is None  # Not returned because is_deleted=True


@pytest.mark.asyncio
async def test_update_resume(resume_service, sample_resume_data):
    from app.schemas.resume import ResumeUpdate

    # Create resume
    resume = await resume_service.create_resume(sample_resume_data)

    # Update resume
    update_data = ResumeUpdate(
        full_name="John Doe", email="john@example.com", phone="+1234567890"
    )

    updated_resume = await resume_service.update_resume(resume.id, update_data)

    assert updated_resume.full_name == "John Doe"
    assert updated_resume.email == "john@example.com"
    assert updated_resume.phone == "+1234567890"
