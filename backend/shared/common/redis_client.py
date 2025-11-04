import redis.asyncio as redis
from typing import Optional
import json
from common.config import BaseConfig

settings = BaseConfig()


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.client.ping()
            print("Redis connected")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.client = None

    async def disconnect(self):
        if self.client:
            await self.client.close()
            print("Redis disconnected")

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    # Token Blacklist Functions

    async def is_token_blacklisted(self, jti: str) -> bool:
        # Check if JWT token ID is blacklisted (revoked)

        if not self.client:
            return False

        try:
            key = f"token_blacklist:{jti}"
            return await self.client.exists(key) > 0
        except Exception as e:
            print(f"Error checking blacklist: {e}")
            return False

    async def blacklist_token(self, jti: str, expires_in: int) -> bool:
        if not self.client:
            return True  # Skip if Redis not available

        try:
            key = f"token_blacklist:{jti}"
            await self.client.setex(key, expires_in, "blacklisted")
            return True
        except Exception as e:
            print(f"Error blacklisting token: {e}")
            return True

    async def store_refresh_token(
        self,
        jti: str,
        user_id: str,
        expires_in: int,
    ) -> bool:
        if not self.client:
            return True  # Skip if Redis not available

        try:
            key = f"refresh_token:{jti}"
            await self.client.setex(key, expires_in, user_id)
            return True
        except Exception as e:
            print(f"Error storing refresh token: {e}")
            return True

    async def get_refresh_token_user(self, jti: str) -> Optional[str]:
        if not self.client:
            return None

        try:
            key = f"refresh_token:{jti}"
            return await self.client.get(key)
        except Exception as e:
            print(f"Error getting refresh token user: {e}")
            return None

    async def revoke_refresh_token(self, jti: str) -> bool:
        if not self.client:
            return True

        try:
            key = f"refresh_token:{jti}"
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"Error revoking refresh token: {e}")
            return True

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        if not self.client:
            return 0

        try:
            pattern = "refresh_token:*"
            cursor = b"0"
            revoked_count = 0

            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern)
                for key in keys:
                    token_user = await self.client.get(key)
                    if token_user == user_id:
                        await self.client.delete(key)
                        revoked_count += 1

                if cursor == b"0":
                    break

            return revoked_count
        except Exception as e:
            print(f"Error revoking user tokens: {e}")
            return 0

    # Cache Functions

    async def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None

        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"Error getting cache: {e}")
            return None

    async def set(self, key: str, value: any, expire: Optional[int] = None):
        if not self.client:
            return

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            print(f"Error setting cache: {e}")

    async def delete(self, key: str):
        if not self.client:
            return

        try:
            await self.client.delete(key)
        except Exception as e:
            print(f"Error deleting cache: {e}")

    async def exists(self, key: str) -> bool:
        if not self.client:
            return False

        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            print(f"Error checking key existence: {e}")
            return False


redis_client = RedisClient(redis_url=settings.redis_url)


async def init_redis():
    await redis_client.connect()


async def close_redis():
    await redis_client.disconnect()
