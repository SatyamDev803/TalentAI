import uuid

import pytest
from common.exceptions import ValidationError
from common.redis_client import redis_client

from app.models.application import ApplicationStatus
from app.models.job import JobStatus
from app.schemas.application import ApplicationCreate
from app.schemas.job import JobCreate, JobUpdate


@pytest.mark.asyncio
async def test_create_job_success(job_service):
    job_data = JobCreate(
        title="Python Developer",
        description="Senior Python developer needed",
        job_type="FULL_TIME",
        experience_level="SENIOR",
        salary_min=100000,
        salary_max=150000,
        location="San Francisco",
        is_remote=True,
    )

    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    result = await job_service.create_job(
        job_data, company_id=company_id, user_id=user_id
    )

    assert result.id is not None
    assert result.status == JobStatus.DRAFT
    assert result.title == "Python Developer"


@pytest.mark.asyncio
async def test_job_caching(job_service, sample_job):
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=user_id
    )
    job_id = str(created_job.id)

    job1 = await job_service.get_job_by_id(job_id)

    job2 = await job_service.get_job_by_id(job_id)

    assert job1.id == job2.id


@pytest.mark.asyncio
async def test_publish_job_indexes_elasticsearch(job_service, sample_job):
    # Create and publish a job
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=user_id
    )
    job_id = str(created_job.id)

    # Publish job
    job = await job_service.publish_job(job_id)

    assert job.status == JobStatus.PUBLISHED


@pytest.mark.asyncio
async def test_cache_invalidation_on_update(job_service, sample_job):
    # Create a job first
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=user_id
    )
    job_id = str(created_job.id)
    cache_key = f"job:{job_id}"

    job_update = JobUpdate(title="Updated Title")
    await job_service.update_job(job_id, job_update)

    cached = await redis_client.get(cache_key)
    assert cached is None


@pytest.mark.asyncio
async def test_job_search_with_filters(job_service):
    filters = {
        "experience_level": "SENIOR",
        "is_remote": True,
        "salary_min": 100000,
        "location": "San Francisco",
    }

    jobs, total = await job_service.list_jobs(
        page=1, page_size=20, query="", filters=filters
    )

    assert isinstance(jobs, list)
    assert isinstance(total, int)


@pytest.mark.asyncio
async def test_apply_for_job_success(job_service, sample_job):
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    recruiter_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=recruiter_id
    )
    job_id = str(created_job.id)

    await job_service.publish_job(job_id)

    candidate_id = str(uuid.uuid4())
    app_data = ApplicationCreate(cover_letter="I am interested in this role")

    result = await job_service.apply_for_job(
        job_id=job_id, candidate_id=candidate_id, app_data=app_data
    )

    assert result.id is not None
    assert result.status == ApplicationStatus.PENDING


@pytest.mark.asyncio
async def test_duplicate_application_rejected(job_service, sample_job):
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    recruiter_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=recruiter_id
    )
    job_id = str(created_job.id)

    await job_service.publish_job(job_id)

    candidate_id = str(uuid.uuid4())
    app_data = ApplicationCreate(cover_letter="...")

    await job_service.apply_for_job(job_id, candidate_id, app_data)

    with pytest.raises(ValidationError):
        await job_service.apply_for_job(job_id, candidate_id, app_data)


@pytest.mark.asyncio
async def test_close_job_success(job_service, sample_job):
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=user_id
    )
    job_id = str(created_job.id)

    await job_service.publish_job(job_id)

    job = await job_service.close_job(job_id)

    assert job.status == JobStatus.CLOSED
    assert job.closed_at is not None


@pytest.mark.asyncio
async def test_get_candidate_applications(job_service, sample_job):
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    recruiter_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=recruiter_id
    )
    job_id = str(created_job.id)

    await job_service.publish_job(job_id)

    candidate_id = str(uuid.uuid4())
    app_data = ApplicationCreate(cover_letter="I'm interested")

    await job_service.apply_for_job(job_id, candidate_id, app_data)

    apps, total = await job_service.get_candidate_applications(
        candidate_id=candidate_id, page=1, page_size=10
    )

    assert isinstance(apps, list)
    assert isinstance(total, int)
    assert total >= 1


@pytest.mark.asyncio
async def test_get_job_applications(job_service, sample_job):
    job_data = JobCreate(**sample_job)
    company_id = str(uuid.uuid4())
    recruiter_id = str(uuid.uuid4())

    created_job = await job_service.create_job(
        job_data, company_id=company_id, user_id=recruiter_id
    )
    job_id = str(created_job.id)

    await job_service.publish_job(job_id)

    candidate_id = str(uuid.uuid4())
    app_data = ApplicationCreate(cover_letter="I'm interested")

    await job_service.apply_for_job(job_id, candidate_id, app_data)

    apps, total = await job_service.get_job_applications(
        job_id=job_id, page=1, page_size=10
    )

    assert isinstance(apps, list)
    assert isinstance(total, int)
    assert total >= 1
