import uuid
import asyncio
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.workspace import DocumentRevision

@celery_app.task(name="create_document_snapshot")
def create_document_snapshot(document_id: str, content: str, edited_by_user_id: str):
    """
    Background worker task to create a historical document revision snapshot.
    """
    async def _async_snapshot():
        async with AsyncSessionLocal() as session:
            revision = DocumentRevision(
                document_id=uuid.UUID(document_id),
                snapshot_content=content,
                edited_by=uuid.UUID(edited_by_user_id)
            )
            session.add(revision)
            await session.commit()
            return str(revision.id)

    # Run the async DB query within the synchronous Celery worker
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.create_task(_async_snapshot())
    else:
        return loop.run_until_complete(_async_snapshot())