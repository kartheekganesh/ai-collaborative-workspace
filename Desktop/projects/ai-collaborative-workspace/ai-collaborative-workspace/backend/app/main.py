from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router

app = FastAPI(title="AI Collaborative Workspace API", version="1.0.0")

@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Register routes
app.include_router(auth_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "online", "database": "connected"}