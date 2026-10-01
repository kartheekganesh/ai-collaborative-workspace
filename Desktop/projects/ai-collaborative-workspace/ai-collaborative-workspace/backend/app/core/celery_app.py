import os
import sys

# Ensure top-level directory is in Python's import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from celery import Celery
from app.core.config import settings

# Retrieve Redis URL from settings or environment fallback
REDIS_URL = getattr(settings, "REDIS_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))

celery_app = Celery(
    "collaborative_workspace_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    # Explicitly include all task modules so Celery registers them on startup
    include=[
        "app.tasks.document_tasks",
        # "app.tasks.ai_tasks", # Uncomment if/when AI tasks module is ready
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Queue routing for background jobs and AI tasks
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "default"},
        "app.tasks.ai.*": {"queue": "ai_tasks"},
        "app.tasks.general.*": {"queue": "default"},
    },
)