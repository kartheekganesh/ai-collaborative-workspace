import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth import router as auth_router
from app.api.v1.workspace import router as workspace_router
from app.core.database import Base, engine


# 1. Lifespan event for async database table initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# 2. Instantiate FastAPI app ONCE
app = FastAPI(
    title="AI Collaborative Workspace API",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. Add CORS Middleware (Fixes "Failed to fetch" browser errors)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. Request Processing Time Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# 5. Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "online", "database": "connected"}


# 6. Static files and Frontend route handling
frontend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend")
)
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