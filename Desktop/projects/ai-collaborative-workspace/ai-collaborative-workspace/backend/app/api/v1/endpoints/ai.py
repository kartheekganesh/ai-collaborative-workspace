import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.workspace import User
from app.tasks.ai_tasks import ping_ai_service
from app.services.vector_search import vector_search_service
from app.services.rag_builder import rag_prompt_builder
from app.services.llm_streamer import llm_streamer

router = APIRouter()


@router.post("/tasks/ping")
async def trigger_ping_task(
    current_user: User = Depends(get_current_user)
):
    """Enqueue a health-check task in the AI queue."""
    task = ping_ai_service.delay()
    return {"task_id": task.id, "status": "Task enqueued"}


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Poll Celery result backend for task status and completion payloads."""
    task_result = AsyncResult(task_id)

    result = None
    if task_result.ready():
        if task_result.successful():
            result = task_result.result
        else:
            # Safely stringify exception to prevent JSON serialization errors
            result = str(task_result.result)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": result
    }


@router.get("/documents/{document_id}/search")
async def search_document_context(
    document_id: uuid.UUID,
    q: str = Query(..., description="Semantic search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


@router.get("/documents/{document_id}/ask/stream")
async def stream_document_ai_query(
    document_id: uuid.UUID,
    prompt: str = Query(..., description="User query for the document AI"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves relevant document context and streams the AI answer via SSE."""
    # 1. Retrieve top-K relevant chunks using pgvector
    chunks = await vector_search_service.retrieve_relevant_chunks(db, document_id, prompt)

    # 2. Assemble prompt with context block
    full_prompt = rag_prompt_builder.build_context_prompt(prompt, chunks)

    # 3. Stream response with appropriate SSE headers to bypass reverse-proxy buffering
    return StreamingResponse(
        llm_streamer.stream_rag_response(full_prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )