# Inside backend/app/api/v1/endpoints/documents.py
from app.tasks.ai_tasks import embed_and_store_document

@router.put("/{workspace_id}/documents/{document_id}")
async def update_document(
    workspace_id: str,
    document_id: str,
    doc_in: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Existing update logic ...
    # ...
    
    # Trigger Celery background embedding task on content update
    if doc_in.content is not None:
        embed_and_store_document.delay(document_id, doc_in.content)

    return updated_document