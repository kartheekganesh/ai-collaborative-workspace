import time
from app.core.celery_app import celery_app

@celery_app.task(name="app.tasks.ai.ping_ai_service", bind=True)
def ping_ai_service(self):
    """Health check task to verify Celery task execution."""
    time.sleep(2)  # Simulate short processing delay
    return {"status": "success", "message": "Celery AI worker is online and responsive!"}

@celery_app.task(name="app.tasks.ai.generate_document_summary", bind=True)
def generate_document_summary(self, document_id: str, content: str):
    """Placeholder for asynchronous document summarization."""
    # Simulation of LLM processing time
    time.sleep(3)
    summary = content[:150] + "..." if len(content) > 150 else content
    return {
        "document_id": document_id,
        "summary": f"AIGenerated Summary: {summary}"
    }