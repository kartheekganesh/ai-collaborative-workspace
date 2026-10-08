import asyncio
import uuid
from app.core.celery_app import celery_app
from app.services.text_chunker import text_chunker
from app.services.embedding_service import embedding_service
from app.core.database import SessionLocal, engine
from app.models.vector import DocumentChunk
from sqlalchemy import delete


@celery_app.task(name="app.tasks.ai.ping_ai_service")
def ping_ai_service():
    return {"status": "online"}


@celery_app.task(name="app.tasks.ai.embed_and_store_document", bind=True)
def embed_and_store_document(self, document_id: str, content: str):
    """Chunk document text, generate embeddings, and store them in pgvector."""

    async def _process():
        try:
            # 1. Split content into text chunks
            chunks = text_chunker.split_text(content)
            async with SessionLocal() as db:
                # Clear old chunks for this document before replacing
                await db.execute(
                    delete(DocumentChunk).where(DocumentChunk.document_id == uuid.UUID(document_id))
                )

                if not chunks:
                    await db.commit()
                    return {"document_id": document_id, "status": "empty_content"}

                # 2. Generate embeddings for all chunks in batch
                embeddings = await embedding_service.get_embeddings(chunks)

                # 3. Save chunks and vectors to Database
                chunk_objects = [
                    DocumentChunk(
                        document_id=uuid.UUID(document_id),
                        chunk_index=idx,
                        content=chunk_text,
                        embedding=vector,
                    )
                    for idx, (chunk_text, vector) in enumerate(zip(chunks, embeddings))
                ]

                db.add_all(chunk_objects)
                await db.commit()

            return {
                "document_id": document_id,
                "status": "success",
                "chunks_processed": len(chunks),
            }
        finally:
            await engine.dispose()

    # Run async function inside Celery's synchronous wrapper
    return asyncio.run(_process())
