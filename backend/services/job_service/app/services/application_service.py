import uuid
from datetime import datetime, timezone
from typing import Optional

from common.exceptions import ResourceNotFoundError, ValidationError
from common.logger import logger
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_for_job(
        self, job_id: str, candidate_id: str, app_data: ApplicationCreate
    ) -> Application:
        """Submit job application"""
        try:
            # Check if job exists
            result = await self.db.execute(
                select(Job).where(Job.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()
            if not job:
                raise ResourceNotFoundError(f"Job {job_id} not found")

            # Check if already applied
            result = await self.db.execute(
                select(Application).where(
                    Application.job_id == uuid.UUID(job_id),
                    Application.candidate_id == uuid.UUID(candidate_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
            )
            existing = result.scalar_one_or_none()
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
            logger.info(f"Application submitted: {application.id}")
            return application
        except (ResourceNotFoundError, ValidationError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error applying for job: {str(e)}")
            raise

    async def get_application_by_id(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        try:
            result = await self.db.execute(
                select(Application).where(Application.id == uuid.UUID(application_id))
            )
            application = result.scalar_one_or_none()
            if not application:
                raise ResourceNotFoundError(f"Application {application_id} not found")
            return application
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching application: {str(e)}")
            raise

    async def get_candidate_applications(
        self, candidate_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Application], int]:
        """Get all applications for a candidate"""
        try:
            # Count total (excluding withdrawn)
            count_result = await self.db.execute(
                select(func.count(Application.id)).where(
                    Application.candidate_id == uuid.UUID(candidate_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
            )
            total = count_result.scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            query = (
                select(Application)
                .where(
                    Application.candidate_id == uuid.UUID(candidate_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
                .order_by(desc(Application.created_at))
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(query)
            applications = result.scalars().all()

            logger.info(f"Retrieved {len(applications)} candidate applications")
            return applications, total
        except Exception as e:
            logger.error(f"Error fetching candidate applications: {str(e)}")
            raise

    async def get_job_applications(
        self, job_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Application], int]:
        """Get all applications for a job"""
        try:
            # Count total (excluding withdrawn)
            count_result = await self.db.execute(
                select(func.count(Application.id)).where(
                    Application.job_id == uuid.UUID(job_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
            )
            total = count_result.scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            query = (
                select(Application)
                .where(
                    Application.job_id == uuid.UUID(job_id),
                    Application.status != ApplicationStatus.WITHDRAWN,
                )
                .order_by(desc(Application.created_at))
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(query)
            applications = result.scalars().all()

            logger.info(f"Retrieved {len(applications)} applications for job {job_id}")
            return applications, total
        except Exception as e:
            logger.error(f"Error fetching job applications: {str(e)}")
            raise

    async def update_application_status(
        self, application_id: str, status_data: ApplicationUpdate
    ) -> Application:
        """Update application status"""
        try:
            application = await self.get_application_by_id(application_id)

            if status_data.status:
                application.status = status_data.status
                if status_data.status != ApplicationStatus.PENDING:
                    application.reviewed_at = datetime.now(timezone.utc)

            if status_data.cover_letter is not None:
                application.cover_letter = status_data.cover_letter

            application.updated_at = datetime.now(timezone.utc)

            self.db.add(application)
            await self.db.commit()
            await self.db.refresh(application)
            logger.info(f"Application updated: {application.id}")
            return application
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating application: {str(e)}")
            raise

    async def withdraw_application(self, application_id: str) -> Application:
        """Withdraw application"""
        try:
            application = await self.get_application_by_id(application_id)
            application.status = ApplicationStatus.WITHDRAWN
            application.updated_at = datetime.now(timezone.utc)

            self.db.add(application)
            await self.db.commit()
            await self.db.refresh(application)
            logger.info(f"Application withdrawn: {application.id}")
            return application
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error withdrawing application: {str(e)}")
            raise
