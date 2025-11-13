"""Redis cache client for Resume Parser Service."""

import json
from typing import Any, Optional
import redis.asyncio as redis

from app.core.config import settings


class RedisCache:
    """Async Redis cache manager."""

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
        """Initialize Redis connection."""
        if not self.enabled:
            print("⚠️  Redis cache is disabled")
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
            print(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")

        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("⚠️  Continuing without cache...")
            self.enabled = False

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            print("✅ Redis connection closed")

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self._client:
            return None

        try:
            cached = await self._client.get(self._make_key(key))
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"⚠️  Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        if not self.enabled or not self._client:
            return False

        try:
            ttl = ttl or self.ttl
            serialized = json.dumps(value, default=str)
            await self._client.setex(self._make_key(key), ttl, serialized)
            return True
        except Exception as e:
            print(f"⚠️  Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled or not self._client:
            return False

        try:
            await self._client.delete(self._make_key(key))
            return True
        except Exception as e:
            print(f"⚠️  Cache delete error: {e}")
            return False

    async def clear_user_cache(self, user_id: str) -> int:
        """Clear all cache entries for a user."""
        if not self.enabled or not self._client:
            return 0

        pattern = self._make_key(f"user:{user_id}:*")
        deleted = 0
        async for key in self._client.scan_iter(match=pattern):
            await self._client.delete(key)
            deleted += 1
        return deleted

    async def get_stats(self) -> dict:
        """Get cache statistics."""
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


# Global cache instance
_cache: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """Get or create cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.initialize()
    return _cache


async def close_cache():
    """Close cache connection."""
    global _cache
    if _cache:
        await _cache.close()
        _cache = None
