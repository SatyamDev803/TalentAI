import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from common.exceptions import ResourceNotFoundError, ValidationError
from common.logger import logger
from common.redis_client import redis_client

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.schemas.application import ApplicationCreate
from app.schemas.job import JobCreate, JobUpdate
from app.services.embedding_service import embedding_service


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        job_data: JobCreate,
        company_id: str,
        user_id: str,
    ) -> Job:

        try:
            category_id = None
            if job_data.category_id:
                try:
                    category_id = uuid.UUID(job_data.category_id)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid category_id: {job_data.category_id}")
                    category_id = None

            job = Job(
                id=uuid.uuid4(),
                title=job_data.title,
                description=job_data.description,
                company_id=uuid.UUID(company_id),
                created_by_id=uuid.UUID(user_id),
                job_type=job_data.job_type,
                experience_level=job_data.experience_level,
                category_id=category_id,
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
        # Get job by ID with caching
        try:
            # Check cache first
            cache_key = f"job:{job_id}"
            cached_job = await redis_client.get(cache_key)
            if cached_job:
                logger.info(f"Job retrieved from cache: {job_id}")
                # Cache hit, skip DB query
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
            await redis_client.set(cache_key, job_dict, expire=3600)

            logger.info(f"Job retrieved from DB: {job_id}")
            return job
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting job: {str(e)}")
            raise

    async def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        query: str = "",
        filters: dict = None,
        current_user: dict = None,
    ) -> Tuple[List[Job], int]:
        # List jobs with role-based filtering
        try:
            if current_user and current_user.get("role") == "ADMIN":
                # Admin sees ALL jobs (DRAFT, PUBLISHED, CLOSED)
                stmt = select(Job).where(Job.deleted_at.is_(None))
            else:
                # Everyone else sees only PUBLISHED
                stmt = select(Job).where(
                    Job.deleted_at.is_(None), Job.status == JobStatus.PUBLISHED
                )

            result = await self.db.execute(stmt)
            all_jobs = result.scalars().all()

            logger.info(f"Found {len(all_jobs)} jobs in database")

            # If no query, return all with pagination
            if not query:
                # Apply filters only
                filtered_jobs = self._apply_filters(all_jobs, filters)
                total = len(filtered_jobs)
                offset = (page - 1) * page_size
                paginated_jobs = filtered_jobs[offset : offset + page_size]

                logger.info(
                    f"Listed {len(paginated_jobs)} jobs (no search, with filters)"
                )
                return paginated_jobs, total

            # SEMANTIC SEARCH
            logger.info(f"Starting semantic search for query: '{query}'")

            # Create embedding for the search query
            query_embedding = embedding_service.embed_query(query)

            # Find similar jobs
            similar_jobs = embedding_service.find_similar_jobs(
                query_embedding=query_embedding,
                jobs=all_jobs,
                top_k=len(all_jobs),
                similarity_threshold=0.25,
            )

            # Extract just the jobs
            ranked_jobs = [job for job, _ in similar_jobs]

            # Apply additional filters
            filtered_jobs = self._apply_filters(ranked_jobs, filters)

            # Pagination
            total = len(filtered_jobs)
            offset = (page - 1) * page_size
            paginated_jobs = filtered_jobs[offset : offset + page_size]

            logger.info(
                f"Semantic search returned {len(paginated_jobs)} jobs (total: {total}, query: '{query}')"
            )
            return paginated_jobs, total

        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return [], 0

    def _apply_filters(self, jobs: list, filters: dict = None) -> list:
        if not filters:
            return jobs

        filtered = jobs

        if filters.get("location"):
            location_query = filters["location"].lower()
            filtered = [j for j in filtered if location_query in j.location.lower()]

        if filters.get("experience_level"):
            exp_level = filters["experience_level"]
            filtered = [j for j in filtered if j.experience_level.value == exp_level]

        if filters.get("job_type"):
            job_type = filters["job_type"]
            filtered = [j for j in filtered if j.job_type.value == job_type]

        if filters.get("salary_min"):
            min_salary = filters["salary_min"]
            filtered = [
                j for j in filtered if j.salary_min and j.salary_min >= min_salary
            ]

        if filters.get("salary_max"):
            max_salary = filters["salary_max"]
            filtered = [
                j for j in filtered if j.salary_max and j.salary_max <= max_salary
            ]

        return filtered

    async def update_job(self, job_id: str, job_data: JobUpdate) -> Job:
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
            await redis_client.delete(f"job:{job_id}")

            logger.info(f"Job updated: {job_id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job: {str(e)}")
            raise

    async def delete_job(self, job_id: str) -> None:
        try:
            job = await self.get_job_by_id(job_id)
            job.deleted_at = datetime.now(timezone.utc)

            await self.db.commit()

            await redis_client.delete(f"job:{job_id}")

            logger.info(f"Job deleted: {job_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting job: {str(e)}")
            raise

    async def publish_job(self, job_id: str) -> Job:
        try:
            job = await self.get_job_by_id(job_id)

            if job.status != JobStatus.DRAFT:
                raise ValidationError("Job must be in DRAFT status to publish")

            job.status = JobStatus.PUBLISHED
            job.published_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(job)

            await redis_client.delete(f"job:{job_id}")

            logger.info(f"Job published: {job_id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error publishing job: {str(e)}")
            raise

    async def close_job(self, job_id: str) -> Job:
        try:
            job = await self.get_job_by_id(job_id)

            if job.status != JobStatus.PUBLISHED:
                raise ValidationError("Only published jobs can be closed")

            job.status = JobStatus.CLOSED
            job.closed_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(job)

            await redis_client.delete(f"job:{job_id}")

            logger.info(f"Job closed: {job_id}")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error closing job: {str(e)}")
            raise

    async def apply_for_job(
        self, job_id: str, candidate_id: str, app_data: ApplicationCreate
    ) -> Application:
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
