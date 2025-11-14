import json
from typing import Any, Optional
import redis.asyncio as redis

from app.core.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    def __init__(self):
        self.enabled = (
            settings.enable_cache if hasattr(settings, "enable_cache") else True
        )
        self.prefix = (
            settings.cache_key_prefix
            if hasattr(settings, "cache_key_prefix")
            else "talentai:resume:"
        )
        self.ttl = (
            settings.redis_cache_ttl if hasattr(settings, "redis_cache_ttl") else 3600
        )
        self._client: Optional[redis.Redis] = None

    async def initialize(self):
        if not self.enabled:
            logger.info("Redis cache is disabled")
            return

        try:
            self._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True,
                socket_keepalive=True,
                socket_connect_timeout=5,
            )

            await self._client.ping()
            logger.info(f"Redis connected: {settings.redis_host}:{settings.redis_port}")

        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            logger.info("Continuing without cache...")
            self.enabled = False

    async def close(self):
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        if not self.enabled or not self._client:
            return None

        try:
            cached = await self._client.get(self._make_key(key))
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.enabled or not self._client:
            return False

        try:
            ttl = ttl or self.ttl
            serialized = json.dumps(value, default=str)
            await self._client.setex(self._make_key(key), ttl, serialized)
            return True
        except Exception as e:
            logger.info(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.enabled or not self._client:
            return False

        try:
            await self._client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_user_cache(self, user_id: str) -> int:
        if not self.enabled or not self._client:
            return 0

        pattern = self._make_key(f"user:{user_id}:*")
        deleted = 0
        async for key in self._client.scan_iter(match=pattern):
            await self._client.delete(key)
            deleted += 1
        return deleted

    async def get_stats(self) -> dict:
        if not self.enabled or not self._client:
            return {"enabled": False}

        try:
            info = await self._client.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            hit_rate = round((hits / total) * 100, 2) if total > 0 else 0.0

            return {
                "enabled": True,
                "hits": hits,
                "misses": misses,
                "hit_rate": hit_rate,
                "keys": await self._client.dbsize(),
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


_cache: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.initialize()
    return _cache


async def close_cache():
    global _cache
    if _cache:
        await _cache.close()
        _cache = None
