import json
from typing import Optional, Any
import aioredis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

class CacheService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        if not self.redis:
            self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        await self.connect()
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        await self.connect()
        await self.redis.set(key, json.dumps(value), ex=ttl_seconds)

    async def invalidate_pattern(self, pattern: str):
        await self.connect()
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

cache_service = CacheService()