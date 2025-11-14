import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(app_dir))

from app.core.celery_app import celery_app


if __name__ == "__main__":
    celery_app.start()
