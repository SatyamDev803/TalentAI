from contextlib import asynccontextmanager

from common.config import BaseConfig
from common.logger import logger
from common.redis_client import close_redis, init_redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import applications, categories, jobs, skills

# Create settings instance
settings = BaseConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle events."""
    logger.info("Starting Job Service...")
    try:
        await init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Redis initialization warning: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Job Service...")
    try:
        await close_redis()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.warning(f"Redis shutdown warning: {e}")


# Create FastAPI app
app = FastAPI(
    title="TalentAI Job Service",
    description="Microservice for managing job postings and applications",
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
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "job-service",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "TalentAI Job Service",
        "docs": "/docs",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
