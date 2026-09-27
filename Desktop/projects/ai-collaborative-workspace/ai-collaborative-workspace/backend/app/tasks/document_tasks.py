from app.core.celery_app import celery_app


@celery_app.task
def process_document(document_id: int):
    """Example task for processing documents."""
    print(f"Processing document {document_id}")
    return {"status": "completed", "document_id": document_id}


@celery_app.task
def create_document_snapshot(document_id: int, workspace_id: int):
    """Create a snapshot of a document."""
    print(f"Creating snapshot for document {document_id} in workspace {workspace_id}")
    return {"status": "snapshot_created", "document_id": document_id, "workspace_id": workspace_id}
