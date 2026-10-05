import uuid
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, Request
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
from app.core.rate_limiter import limiter

router = APIRouter()


class TransformRequest(BaseModel):
    action: str  # e.g., 'rephrase', 'summarize', 'fix_grammar'
    text: str


@router.post("/tasks/ping")
@limiter.limit("10/minute")
async def trigger_ping_task(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Enqueue a health-check task in the AI queue."""
    task = ping_ai_service.delay()
    return {"task_id": task.id, "status": "Task enqueued"}


@router.get("/tasks/{task_id}/status")
@limiter.limit("30/minute")
async def get_task_status(
    request: Request,
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
@limiter.limit("15/minute")
async def search_document_context(
    request: Request,
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
@limiter.limit("5/minute")
async def stream_document_ai_query(
    request: Request,
    document_id: uuid.UUID,
    prompt: str = Query(..., description="User query for the document AI"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves relevant document context and streams the AI answer via SSE."""
    chunks = await vector_search_service.retrieve_relevant_chunks(db, document_id, prompt)
    full_prompt = rag_prompt_builder.build_context_prompt(prompt, chunks)

    return StreamingResponse(
        llm_streamer.stream_rag_response(full_prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/transform")
@limiter.limit("10/minute")
async def transform_text(
    request: Request,
    payload: TransformRequest,
    current_user: User = Depends(get_current_user)
):
    """Applies quick inline AI edits to selected text snippets."""
    action_prompts = {
        "rephrase": "Rephrase the following text to be clear, professional, and concise:",
        "summarize": "Summarize the following text in one crisp sentence:",
        "fix_grammar": "Correct all grammar, spelling, and punctuation errors in the following text:"
    }

    prefix = action_prompts.get(payload.action, "Improve the following text:")
    full_prompt = f"{prefix}\n\n\"{payload.text}\""

    transformed = await llm_streamer.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.2
    )
    
    result_text = transformed.choices[0].message.content.strip('"')
    return {"status": "success", "transformed_text": result_text}