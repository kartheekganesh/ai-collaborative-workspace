import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.workspace import router as workspace_router
from app.api.v1.endpoints import ws, ai
from app.core.database import Base, engine
from app.core.rate_limiter import limiter
from app.core.redis import redis_client
from app.models import vector  # noqa: F401


# 1. Initialize database tables and verify Redis during application startup.
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("ENVIRONMENT") != "production":
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
    try:
        await redis_client.ping()
        yield
    finally:
        await redis_client.aclose()
        await engine.dispose()


# 2. Instantiate FastAPI app
app = FastAPI(
    title="AI Collaborative Workspace API",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. Configure Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 4. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 5. Request Processing Time Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# 6. Include Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1", tags=["WebSockets"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Engine"])


@app.get("/health", tags=["Health"])
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await redis_client.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="A required service is unavailable",
        ) from exc
    return {"status": "online", "database": "connected", "redis": "connected"}


# 7. Static files and Frontend route handling
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
index_file_path = os.path.join(frontend_path, "index.html")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    if os.path.exists(index_file_path):
        return FileResponse(index_file_path)
    return JSONResponse(
        content={
            "status": "online",
            "message": "AI Collaborative Workspace API is running",
            "docs_url": "/docs",
        }
    )
