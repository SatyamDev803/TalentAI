"""FastAPI application for Auth Service."""

from contextlib import asynccontextmanager

from common.config import BaseConfig
from common.redis_client import close_redis, init_redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, companies, users

settings = BaseConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle events."""
    # Startup
    print("�� Starting Auth Service...")
    try:
        await init_redis()
        print("✅ Redis initialized (or skipped if unavailable)")
    except Exception as e:
        print(f"⚠️  Redis initialization warning: {e}")

    yield

    # Shutdown
    print("🛑 Shutting down Auth Service...")
    try:
        await close_redis()
        print("✅ Redis disconnected")
    except Exception as e:
        print(f"⚠️  Redis shutdown warning: {e}")


# Create FastAPI app
app = FastAPI(
    title="TalentAI Auth Service",
    description="Authentication and user management service",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
cors_origins = ["*"]  # Allow all for local dev
if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS:
    cors_origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "TalentAI Auth Service",
        "docs": "/docs",
        "version": "1.0.0",
    }
