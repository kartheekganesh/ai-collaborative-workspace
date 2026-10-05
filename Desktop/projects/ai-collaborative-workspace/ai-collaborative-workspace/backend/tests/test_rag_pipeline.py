import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import SessionLocal
from app.models.vector import DocumentChunk
from sqlalchemy import select

@pytest.mark.asyncio
async def test_full_rag_pipeline(test_user_token, test_document_id):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 1. Update document content to trigger Celery background chunking/embedding
        sample_text = (
            "The AI-Powered Collaborative Workspace uses FastAPI for high-performance REST APIs. "
            "It integrates Celery and Redis to handle heavy AI background processing asynchronously. "
            "Vector embeddings are stored in PostgreSQL using the pgvector extension."
        )
        response = await ac.put(
            f"/api/v1/workspaces/test-ws/documents/{test_document_id}",
            json={"content": sample_text},
            headers=headers
        )
        assert response.status_code == 200

        # Wait briefly for Celery background worker to process chunks and vectors
        await asyncio.sleep(3)

        # 2. Verify chunks and vector embeddings were written to pgvector
        async with SessionLocal() as db:
            result = await db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == test_document_id)
            )
            chunks = result.scalars().all()
            assert len(chunks) > 0
            assert chunks[0].embedding is not None

        # 3. Test Vector Search Endpoint
        search_res = await ac.get(
            f"/api/v1/ai/documents/{test_document_id}/search?q=What database handles vectors?",
            headers=headers
        )
        assert search_res.status_code == 200
        data = search_res.json()
        assert data["results_count"] > 0
        assert "pgvector" in data["chunks"][0]["content"]

        # 4. Test SSE Streaming Response Endpoint
        async with ac.stream(
            "GET",
            f"/api/v1/ai/documents/{test_document_id}/ask/stream?prompt=Summarize+the+tech+stack",
            headers=headers
        ) as stream_res:
            assert stream_res.status_code == 200
            content = await stream_res.aread()
            assert b"data:" in content