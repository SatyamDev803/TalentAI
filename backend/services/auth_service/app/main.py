from contextlib import asynccontextmanager

from common.config import BaseConfig
from common.logger import logger
from common.redis_client import close_redis, init_redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, companies, users

settings = BaseConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")
    try:
        await init_redis()
    except Exception as e:
        logger.warning(f"Redis initialization warning: {e}")

    yield
    logger.info("Shutting down Auth Service...")
    try:
        await close_redis()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.warning(f"Redis shutdown warning: {e}")


app = FastAPI(
    title="TalentAI Auth Service",
    description="Microservice for authentication and user management",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = ["*"]  # Allow all for local dev
if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS:
    cors_origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "auth-service"}


@app.get("/", tags=["Root"])
async def root():
    return {"message": "TalentAI Auth Service", "docs": "/docs"}
