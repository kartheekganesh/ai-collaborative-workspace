import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class CacheService:
    def __init__(self):
        self.redis: redis.Redis | None = None

    async def connect(self):
        if not self.redis:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        await self.connect()
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        await self.connect()
        await self.redis.set(key, json.dumps(value), ex=ttl_seconds)

    async def invalidate_pattern(self, pattern: str):
        await self.connect()
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)

    async def close(self):
        if self.redis:
            await self.redis.aclose()
            self.redis = None


cache_service = CacheService()
