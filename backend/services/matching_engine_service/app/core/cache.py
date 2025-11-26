import json
import sys
from pathlib import Path
from typing import Optional, Any, Dict
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.redis_client import redis_client
from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class CacheService:

    def __init__(self):
        self.client = redis_client
        self.ttl = settings.redis_cache_ttl
        self.prefix = "talentai:matching:"
        self.enabled = settings.enable_cache

        self.hit_count = 0
        self.miss_count = 0

        logger.info(
            f"CacheService initialized (enabled={self.enabled}, "
            f"ttl={self.ttl}s, prefix='{self.prefix}')"
        )

    def _make_key(self, key: str) -> str:

        return f"{self.prefix}{key}"

    def _hash_key(self, data: Any) -> str:

        try:
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(json_str.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Hash key generation failed: {e}")
            return f"error_{id(data)}"

    async def get(self, key: str) -> Optional[Any]:

        if not self.enabled:
            return None

        full_key = self._make_key(key)

        try:
            data = await self.client.get(full_key)
            if data:
                self.hit_count += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(data)
            else:
                self.miss_count += 1
                logger.debug(f"Cache MISS: {key}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Cache get JSON decode error for key '{key}': {e}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}", exc_info=True)
            return None

    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:

        if not self.enabled:
            return False

        full_key = self._make_key(key)
        expire_time = ttl if ttl is not None else self.ttl

        try:
            json_data = json.dumps(data, default=str)
            await self.client.set(full_key, json_data, expire=expire_time)
            logger.debug(f"Cache SET: {key} (ttl={expire_time}s)")
            return True

        except (TypeError, json.JSONEncodeError) as e:
            logger.error(f"Cache set JSON encode error for key '{key}': {e}")
            return False
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:

        if not self.enabled:
            return False

        full_key = self._make_key(key)

        try:
            if self.client.client:
                await self.client.client.delete(full_key)
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}", exc_info=True)
            return False

    async def invalidate(self, pattern: str = "*") -> int:

        if not self.enabled:
            return 0

        full_pattern = self._make_key(pattern)

        try:
            if not self.client.client:
                logger.warning("Redis client not available for invalidation")
                return 0

            keys = await self.client.client.keys(full_pattern)

            if keys:
                deleted_count = await self.client.client.delete(*keys)
                logger.info(
                    f"Cache invalidated: {deleted_count} keys matching '{pattern}'"
                )
                return deleted_count
            else:
                logger.debug(f"No keys found matching pattern '{pattern}'")
                return 0

        except Exception as e:
            logger.error(
                f"Cache invalidate error for pattern '{pattern}': {e}", exc_info=True
            )
            return 0

    async def get_match(
        self, job_id: str, candidate_id: Optional[str] = None
    ) -> Optional[dict]:

        key_suffix = (
            f"match:job:{job_id}:candidate:{candidate_id}"
            if candidate_id
            else f"match:job:{job_id}"
        )
        return await self.get(key_suffix)

    async def set_match(
        self,
        job_id: str,
        data: dict,
        candidate_id: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> bool:

        key_suffix = (
            f"match:job:{job_id}:candidate:{candidate_id}"
            if candidate_id
            else f"match:job:{job_id}"
        )
        return await self.set(key_suffix, data, ttl)

    async def invalidate_job_matches(self, job_id: str) -> int:

        return await self.invalidate(f"match:job:{job_id}:*")

    async def invalidate_candidate_matches(self, candidate_id: str) -> int:

        return await self.invalidate(f"match:*:candidate:{candidate_id}")

    async def get_detailed_stats(self) -> Dict[str, Any]:
        try:
            total_requests = self.hit_count + self.miss_count
            hit_rate = 0.0
            if total_requests > 0:
                hit_rate = (self.hit_count / total_requests) * 100

            redis_stats = {}
            if self.client and self.client.client:
                try:
                    info = await self.client.client.info("stats")
                    redis_stats = {
                        "redis_total_connections": info.get(
                            "total_connections_received", 0
                        ),
                        "redis_commands_processed": info.get(
                            "total_commands_processed", 0
                        ),
                    }
                except Exception as e:
                    redis_stats = {"error": f"Could not fetch Redis stats: {e}"}

            return {
                "enabled": self.enabled,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl,
                "prefix": self.prefix,
                "redis_connected": self.client is not None
                and self.client.client is not None,
                **redis_stats,
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_llm_skill_gap(
        self, job_id: str, candidate_id: str, default: dict = None
    ) -> Optional[dict]:

        cache_key = f"{job_id}-{candidate_id}"
        result = await self.get(f"llm:skill_gap:{cache_key}")
        return result if result is not None else default

    async def cache_llm_skill_gap(
        self, job_id: str, candidate_id: str, data: dict, ttl: int = 86400
    ) -> bool:

        cache_key = f"{job_id}-{candidate_id}"
        return await self.set(f"llm:skill_gap:{cache_key}", data, ttl)

    async def get_llm_explanation(
        self, job_id: str, candidate_id: str, default: dict = None
    ) -> Optional[dict]:

        cache_key = f"{job_id}-{candidate_id}"
        result = await self.get(f"llm:explanation:{cache_key}")
        return result if result is not None else default

    async def cache_llm_explanation(
        self, job_id: str, candidate_id: str, data: dict, ttl: int = 86400
    ) -> bool:

        cache_key = f"{job_id}-{candidate_id}"
        return await self.set(f"llm:explanation:{cache_key}", data, ttl)

    async def get_llm_recommendation(
        self, job_id: str, candidate_id: str, default: dict = None
    ) -> Optional[dict]:

        cache_key = f"{job_id}-{candidate_id}"
        result = await self.get(f"llm:recommendation:{cache_key}")
        return result if result is not None else default

    async def cache_llm_recommendation(
        self, job_id: str, candidate_id: str, data: dict, ttl: int = 86400
    ) -> bool:

        cache_key = f"{job_id}-{candidate_id}"
        return await self.set(f"llm:recommendation:{cache_key}", data, ttl)


cache_service = CacheService()
