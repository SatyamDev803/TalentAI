import time
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.batch import BatchUploadResult, BatchUploadResponse
from app.schemas.resume import ResumeCreate
from app.services.resume_service import ResumeService
from app.core.config import settings
from common.logging import get_logger

logger = get_logger(__name__)

# Configuration
MAX_BATCH_SIZE = 10
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


class BatchService:

    def __init__(self, db: AsyncSession):

        self.db = db
        self.resume_service = ResumeService(db)

    async def batch_upload_resumes(
        self,
        files: List[UploadFile],
        user_id: uuid.UUID,
        upload_dir: Path,
    ) -> BatchUploadResponse:

        start_time = time.time()

        logger.info(f"Batch upload: {len(files)} files from user {user_id}")

        # Validate batch size
        if len(files) > MAX_BATCH_SIZE:
            logger.warning(f"Batch too large: {len(files)} > {MAX_BATCH_SIZE}")
            return BatchUploadResponse(
                total_files=len(files),
                uploaded=0,
                failed=len(files),
                skipped=0,
                results=[
                    BatchUploadResult(
                        filename=f.filename or "unknown",
                        status="failed",
                        error=f"Batch size exceeds maximum ({MAX_BATCH_SIZE})",
                    )
                    for f in files
                ],
                processing_time_seconds=time.time() - start_time,
            )

        # Process each file
        results = []
        uploaded_count = 0
        failed_count = 0
        skipped_count = 0

        for file in files:
            result = await self._process_single_file(file, user_id, upload_dir)
            results.append(result)

            if result.status == "uploaded":
                uploaded_count += 1
            elif result.status == "failed":
                failed_count += 1
            elif result.status == "skipped":
                skipped_count += 1

        processing_time = time.time() - start_time

        logger.info(
            f"Batch upload complete: "
            f"{uploaded_count} uploaded, "
            f"{failed_count} failed, "
            f"{skipped_count} skipped "
            f"in {processing_time:.2f}s"
        )

        return BatchUploadResponse(
            total_files=len(files),
            uploaded=uploaded_count,
            failed=failed_count,
            skipped=skipped_count,
            results=results,
            processing_time_seconds=round(processing_time, 3),
        )

    async def _process_single_file(
        self,
        file: UploadFile,
        user_id: uuid.UUID,
        upload_dir: Path,
    ) -> BatchUploadResult:
        filename = file.filename or "unknown"

        try:
            validation_error = self._validate_file(file)
            if validation_error:
                logger.warning(f"{filename}: {validation_error}")
                return BatchUploadResult(
                    filename=filename,
                    status="skipped",
                    error=validation_error,
                )

            # Read file content
            content = await file.read()
            file_size = len(content)

            # Check file size
            if file_size > MAX_FILE_SIZE:
                return BatchUploadResult(
                    filename=filename,
                    status="skipped",
                    error=f"File too large ({file_size / 1024 / 1024:.1f}MB > 10MB)",
                    file_size=file_size,
                )

            # Determine file type
            file_extension = Path(filename).suffix.lower()
            file_type = "pdf" if file_extension == ".pdf" else "docx"

            # Create unique filename
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Create user directory with "resumes" subdirectory
            user_dir = upload_dir / "resumes" / str(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = user_dir / unique_filename
            with open(file_path, "wb") as f:
                f.write(content)

            logger.info(f"File saved to: {file_path}")

            # Create resume record
            resume_data = ResumeCreate(
                user_id=user_id,
                filename=filename,
                file_path=f"uploads/resumes/{user_id}/{unique_filename}",
                file_size=file_size,
                file_type=file_type,
            )

            resume = await self.resume_service.create_resume(resume_data)

            # Queue for async parsing
            queued = await self._queue_parsing_task(resume.id)

            logger.info(f"{filename}: Uploaded successfully")

            return BatchUploadResult(
                filename=filename,
                resume_id=resume.id,
                status="uploaded",
                file_size=file_size,
                queued_for_parsing=queued,
            )

        except Exception as e:
            logger.error(f"{filename}: Error - {str(e)}", exc_info=True)
            return BatchUploadResult(
                filename=filename,
                status="failed",
                error=f"Upload error: {str(e)}",
            )

    def _validate_file(self, file: UploadFile) -> str | None:

        if not file.filename:
            return "No filename provided"

        # Check extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            return f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Check content type
        if file.content_type:
            valid_content_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ]
            if file.content_type not in valid_content_types:
                return f"Invalid content type: {file.content_type}"

        return None

    async def _queue_parsing_task(self, resume_id: uuid.UUID) -> bool:

        if not hasattr(settings, "CELERY_ENABLED") or not settings.CELERY_ENABLED:
            logger.warning("Celery not configured, skipping task queue")
            return False

        try:
            from app.tasks.parsing_tasks import parse_resume_async

            # Queue task
            task = parse_resume_async.delay(str(resume_id))

            logger.info(f"Queued parsing task {task.id} for resume {resume_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to queue task: {str(e)}")
            return False
