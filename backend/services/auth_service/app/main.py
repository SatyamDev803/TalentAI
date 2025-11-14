from contextlib import asynccontextmanager

from common.config import BaseConfig
from common.logging import get_logger, setup_logging
from common.redis_client import close_redis, init_redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, companies, users

settings = BaseConfig()

setup_logging(
    service_name="auth",
    log_level=settings.log_level,
    log_format="json" if settings.is_production else "text",
    enable_file_logging=not settings.is_production,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AUTH SERVICE STARTING")

    try:
        await init_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis initialization warning: {e}")

    yield

    logger.info("AUTH SERVICE SHUTTING DOWN")
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Redis shutdown warning: {e}")


app = FastAPI(
    title="TalentAI Auth Service",
    description="Microservice for authentication and user management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {"message": "TalentAI Job Service", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "job-service"}
