from datetime import datetime, timezone
import uuid
from typing import Optional


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(dt_str) if dt_str else None
