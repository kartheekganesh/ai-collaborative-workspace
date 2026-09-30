import redis.asyncio as aioredis
from app.core.config import settings # Assuming REDIS_URL is configured

redis_client = aioredis.from_url("redis://redis:6379/0", decode_responses=True)

async def get_redis():
    return redis_client