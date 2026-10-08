from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


def user_or_ip_key_func(request: Request) -> str:
    """Uses authenticated user ID as rate limit key, falling back to client IP address."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1][:20]  # First 20 chars of token as identifier
    return get_remote_address(request)


limiter = Limiter(
    key_func=user_or_ip_key_func, storage_uri=REDIS_URL, default_limits=["100/minute"]
)
