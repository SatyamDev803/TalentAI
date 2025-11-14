from contextlib import asynccontextmanager

from common.config import BaseConfig
from common.redis_client import close_redis, init_redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import applications, categories, jobs, skills
from common.logging import get_logger, setup_logging

settings = BaseConfig()

setup_logging(
    service_name="job",
    log_level=settings.log_level,
    log_format="json" if settings.is_production else "text",
    enable_file_logging=not settings.is_production,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("JOB SERVICE STARTING")
    try:
        await init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Redis initialization warning: {e}")

    yield

    logger.info("JOB SERVICE SHUTTING DOWN")
    try:
        await close_redis()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.warning(f"Redis shutdown warning: {e}")


app = FastAPI(
    title="TalentAI Job Service",
    description="Microservice for managing job postings and applications",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {"message": "TalentAI Job Service", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "job-service"}
