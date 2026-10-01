from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from app.tasks.ai_tasks import ping_ai_service, generate_document_summary
from app.core.security import get_current_user

router = APIRouter()

@router.post("/tasks/ping")
async def trigger_ping_task(current_user: dict = Depends(get_current_user)):
    """Enqueue a health-check task in the AI queue."""
    task = ping_ai_service.delay()
    return {"task_id": task.id, "status": "Task enqueued"}

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str, current_user: dict = Depends(get_current_user)):
    """Poll Celery result backend for task status and completion payloads."""
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    return response