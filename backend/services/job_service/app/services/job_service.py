import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from common.exceptions import ResourceNotFoundError, ValidationError
from common.logger import logger
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.schemas.application import ApplicationCreate
from app.schemas.job import JobCreate, JobUpdate
from app.utils.cache import cache_manager
from app.utils.search import search_manager


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        job_data: JobCreate,
        company_id: str,
        user_id: str,
    ) -> Job:
        """Create a new job"""
        try:
            job = Job(
                id=uuid.uuid4(),
                title=job_data.title,
                description=job_data.description,
                company_id=uuid.UUID(company_id),
                created_by_id=uuid.UUID(user_id),
                job_type=job_data.job_type,
                experience_level=job_data.experience_level,
                category_id=(
                    uuid.UUID(job_data.category_id) if job_data.category_id else None
                ),
                salary_min=job_data.salary_min,
                salary_max=job_data.salary_max,
                location=job_data.location,
                is_remote=job_data.is_remote,
                status=JobStatus.DRAFT,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            logger.info(f"Job created: {job.id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {str(e)}")
            raise

    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID with caching"""
        try:
            # Check cache first
            cache_key = f"job:{job_id}"
            cached_job = await cache_manager.get(cache_key)
            if cached_job:
                logger.info(f"Job retrieved from cache: {job_id}")
                # Cache hit - skip DB query
                # But still return Job object from DB for consistency

            # Query database (always for consistency)
            stmt = select(Job).where(
                Job.id == uuid.UUID(job_id), Job.deleted_at.is_(None)
            )
            result = await self.db.execute(stmt)
            job = result.scalars().first()

            if not job:
                raise ResourceNotFoundError(f"Job {job_id} not found")

            # Cache result (TTL: 1 hour)
            job_dict = {
                "id": str(job.id),
                "title": job.title,
                "description": job.description,
                "status": job.status.value,
                "location": job.location,
                "is_remote": job.is_remote,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
            }
            await cache_manager.set(cache_key, job_dict, ttl=3600)

            logger.info(f"Job retrieved from DB: {job_id}")
            return job
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting job: {str(e)}")
            raise

    async def list_jobs(
        self, page: int = 1, page_size: int = 20, query: str = "", filters: dict = None
    ) -> Tuple[List[Job], int]:
        """List published jobs with Elasticsearch"""
        try:
            # Use Elasticsearch for search
            results = await search_manager.search_jobs(
                query=query, filters=filters or {}, page=page, page_size=page_size
            )

            logger.info(f"Listed {len(results['jobs'])} jobs")
            return results["jobs"], results["total"]
        except Exception as e:
            logger.error(f"Error listing jobs: {str(e)}")
            raise

    async def update_job(self, job_id: str, job_data: JobUpdate) -> Job:
        """Update job"""
        try:
            job = await self.get_job_by_id(job_id)

            # Update fields
            if job_data.title:
                job.title = job_data.title
            if job_data.description:
                job.description = job_data.description
            if job_data.salary_min:
                job.salary_min = job_data.salary_min
            if job_data.salary_max:
                job.salary_max = job_data.salary_max
            if job_data.location:
                job.location = job_data.location
            if job_data.is_remote is not None:
                job.is_remote = job_data.is_remote

            job.updated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(job)

            # Clear cache
            await cache_manager.delete(f"job:{job_id}")

            logger.info(f"Job updated: {job_id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job: {str(e)}")
            raise

    async def delete_job(self, job_id: str) -> None:
        """Delete job (soft delete)"""
        try:
            job = await self.get_job_by_id(job_id)
            job.deleted_at = datetime.now(timezone.utc)

            await self.db.commit()

            # Clear cache and ES
            await cache_manager.delete(f"job:{job_id}")
            await search_manager.delete_job(job_id)

            logger.info(f"Job deleted: {job_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting job: {str(e)}")
            raise

    async def publish_job(self, job_id: str) -> Job:
        """Publish job"""
        try:
            job = await self.get_job_by_id(job_id)

            if job.status != JobStatus.DRAFT:
                raise ValidationError("Job must be in DRAFT status to publish")

            job.status = JobStatus.PUBLISHED
            job.published_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(job)

            # Index in Elasticsearch
            await search_manager.index_job(job.__dict__)

            # Clear cache
            await cache_manager.delete(f"job:{job_id}")

            logger.info(f"Job published: {job_id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error publishing job: {str(e)}")
            raise

    async def close_job(self, job_id: str) -> Job:
        """Close job"""
        try:
            job = await self.get_job_by_id(job_id)

            if job.status != JobStatus.PUBLISHED:
                raise ValidationError("Only published jobs can be closed")

            job.status = JobStatus.CLOSED
            job.closed_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(job)

            # Clear cache
            await cache_manager.delete(f"job:{job_id}")

            logger.info(f"Job closed: {job_id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error closing job: {str(e)}")
            raise

    async def apply_for_job(
        self, job_id: str, candidate_id: str, app_data: ApplicationCreate
    ) -> Application:
        """Apply for job"""
        try:
            # Check if already applied
            stmt = select(Application).where(
                Application.job_id == uuid.UUID(job_id),
                Application.candidate_id == uuid.UUID(candidate_id),
                Application.status != ApplicationStatus.WITHDRAWN,
            )
            result = await self.db.execute(stmt)
            existing = result.scalars().first()

            if existing:
                raise ValidationError("You have already applied for this job")

            application = Application(
                id=uuid.uuid4(),
                job_id=uuid.UUID(job_id),
                candidate_id=uuid.UUID(candidate_id),
                cover_letter=app_data.cover_letter,
                status=ApplicationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            self.db.add(application)
            await self.db.commit()
            await self.db.refresh(application)

            logger.info(f"Application created: {application.id}")
            return application
        except (ValidationError, ResourceNotFoundError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error applying for job: {str(e)}")
            raise

    async def get_candidate_applications(
        self, candidate_id: str, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Application], int]:
        """Get candidate applications"""
        try:
            count_stmt = select(func.count(Application.id)).where(
                Application.candidate_id == uuid.UUID(candidate_id),
                Application.status != ApplicationStatus.WITHDRAWN,
            )
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar() or 0

            offset = (page - 1) * page_size
            stmt = (
                select(Application)
                .where(
                    Application.candidate_id == uuid.UUID(candidate_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
                .order_by(desc(Application.created_at))
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(stmt)
            applications = result.scalars().all()

            return applications, total
        except Exception as e:
            logger.error(f"Error getting applications: {str(e)}")
            raise

    async def get_job_applications(
        self, job_id: str, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Application], int]:
        """Get job applications"""
        try:
            count_stmt = select(func.count(Application.id)).where(
                Application.job_id == uuid.UUID(job_id),
                Application.status != ApplicationStatus.WITHDRAWN,
            )
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar() or 0

            offset = (page - 1) * page_size
            stmt = (
                select(Application)
                .where(
                    Application.job_id == uuid.UUID(job_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
                .order_by(desc(Application.created_at))
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(stmt)
            applications = result.scalars().all()

            return applications, total
        except Exception as e:
            logger.error(f"Error getting job applications: {str(e)}")
            raise
