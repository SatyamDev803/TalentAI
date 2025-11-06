import json
from typing import Optional

import redis.asyncio as redis

from common.config import BaseConfig
from common.logger import logger

settings = BaseConfig()


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self.client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.client = None

    async def disconnect(self):
        if self.client:
            try:
                await self.client.close()
                logger.info("Redis disconnected")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def is_token_blacklisted(self, jti: str) -> bool:
        if not self.client:
            return False
        try:
            return await self.client.exists(f"token_blacklist:{jti}") > 0
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False

    async def blacklist_token(self, jti: str, expires_in: int) -> bool:
        if not self.client:
            return True
        try:
            await self.client.setex(f"token_blacklist:{jti}", expires_in, "blacklisted")
            return True
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return True

    async def store_refresh_token(
        self, jti: str, user_id: str, expires_in: int
    ) -> bool:
        if not self.client:
            return True
        try:
            await self.client.setex(f"refresh_token:{jti}", expires_in, user_id)
            return True
        except Exception as e:
            logger.error(f"Error storing refresh token: {e}")
            return True

    async def get_refresh_token_user(self, jti: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            return await self.client.get(f"refresh_token:{jti}")
        except Exception as e:
            logger.error(f"Error getting refresh token: {e}")
            return None

    async def revoke_refresh_token(self, jti: str) -> bool:
        if not self.client:
            return True
        try:
            await self.client.delete(f"refresh_token:{jti}")
            return True
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return True

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        if not self.client:
            return 0

        try:
            pattern = "refresh_token:*"
            keys = await self.client.keys(pattern)

            revoked_count = 0
            for key in keys:
                token_user = await self.client.get(key)
                if token_user == user_id:
                    await self.client.delete(key)
                    revoked_count += 1

            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return 0

    async def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None

    async def set(self, key: str, value: any, expire: Optional[int] = None):
        if not self.client:
            return
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    async def delete(self, key: str):
        if not self.client:
            return
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")

    async def exists(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key: {e}")
            return False


redis_client = RedisClient(redis_url=settings.redis_url)


async def init_redis():
    await redis_client.connect()


async def close_redis():
    await redis_client.disconnect()
