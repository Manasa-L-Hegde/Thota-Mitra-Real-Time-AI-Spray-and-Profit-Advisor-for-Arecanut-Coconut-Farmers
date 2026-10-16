import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import router as api_router

from contextlib import asynccontextmanager
from app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and seed records
    # TestClient exercises an already-initialized test database; avoiding a
    # redundant DDL/seed transaction prevents OneDrive SQLite lock contention.
    if not os.getenv("PYTEST_CURRENT_TEST"):
        init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Decision support system for arecanut and coconut farmers in Karnataka. "
        "Real-time monsoon fruit rot (koleroga) risk scoring and spray window advisory."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for local development and web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Azure App Service and monitoring."""
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Mount static folder if it exists (for dashboard files)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
