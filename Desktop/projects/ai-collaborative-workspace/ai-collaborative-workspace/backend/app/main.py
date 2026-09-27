from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.workspace import router as workspace_router

app = FastAPI(title="AI Collaborative Workspace API", version="1.0.0")

@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "online", "database": "connected"}

import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response