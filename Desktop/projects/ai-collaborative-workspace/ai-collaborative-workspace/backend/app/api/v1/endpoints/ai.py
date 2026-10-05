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

# In backend/app/api/v1/endpoints/ai.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.vector_search import vector_search_service
from app.services.rag_builder import rag_prompt_builder

@router.get("/documents/{document_id}/search")
async def search_document_context(
    document_id: str,
    q: str = Query(..., description="Semantic search query"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Performs vector similarity search against document chunks and constructs RAG context."""
    chunks = await vector_search_service.retrieve_relevant_chunks(db, document_id, q)
    formatted_prompt = rag_prompt_builder.build_context_prompt(q, chunks)
    
    return {
        "document_id": document_id,
        "query": q,
        "results_count": len(chunks),
        "chunks": chunks,
        "constructed_prompt_preview": formatted_prompt
    }