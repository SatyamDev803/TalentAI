"""Celery tasks package."""

from app.tasks.parsing_tasks import (
    parse_resume_async,
    batch_parse_resumes_async,
)

__all__ = [
    "parse_resume_async",
    "batch_parse_resumes_async",
]
