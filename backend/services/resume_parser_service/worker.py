"""Celery worker entry point."""

import sys
from pathlib import Path

# Add app to path
app_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(app_dir))

from app.core.celery_app import celery_app

# Import tasks to register them
from app.tasks import parsing_tasks  # noqa

if __name__ == "__main__":
    celery_app.start()
