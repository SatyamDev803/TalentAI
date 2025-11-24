import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.redis_client import redis_client
from app.core.config import settings


class CacheService:

    def __init__(self):
        self.client = redis_client
        self.ttl = settings.redis_cache_ttl
        self.prefix = "talentai:matching:"
        self.enabled = settings.enable_cache

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get_match(self, job_id: str, candidate_id: str = None) -> Optional[dict]:
        if not self.enabled:
            return None

        key_suffix = (
            f"job:{job_id}:candidate:{candidate_id}"
            if candidate_id
            else f"job:{job_id}"
        )
        key = self._make_key(key_suffix)

        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set_match(self, job_id: str, data: dict, candidate_id: str = None):
        if not self.enabled:
            return

        key_suffix = (
            f"job:{job_id}:candidate:{candidate_id}"
            if candidate_id
            else f"job:{job_id}"
        )
        key = self._make_key(key_suffix)

        try:
            await self.client.set(key, json.dumps(data), expire=self.ttl)
        except Exception as e:
            print(f"Cache set error: {e}")

    async def invalidate(self, pattern: str = "*"):
        if not self.enabled:
            return

        full_pattern = self._make_key(pattern)
        try:
            keys = (
                await self.client.client.keys(full_pattern)
                if self.client.client
                else []
            )
            if keys:
                await self.client.client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidate error: {e}")


cache_service = CacheService()
