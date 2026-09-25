from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import workspace  # Ensures models are imported before Base creation

app = FastAPI(title="AI Collaborative Workspace API", version="1.0.0")

@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "online", "database": "connected"}