import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import psutil


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from sqlalchemy import text

from common.logging import get_logger, setup_logging
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.websocket import sio
from app.db.session import async_engine, get_db
from app.middleware.performance import PerformanceMonitoringMiddleware
from app.utils.embedding_generator import preload_model


setup_logging(
    service_name="resume_parser",
    log_level=settings.log_level,
    log_format="json" if settings.is_production else "text",
    enable_file_logging=not settings.is_production,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RESUME PARSER SERVICE STARTING")

    preload_model()

    # Track startup time for health check
    app.state.start_time = time.time()

    yield

    logger.info("RESUME PARSER SERVICE SHUTTING DOWN")

    # Cleanup ML resources
    try:
        from joblib.externals.loky import get_reusable_executor

        executor = get_reusable_executor()
        executor.shutdown(wait=True, kill_workers=True)
    except Exception:
        pass

    # Allow threads to cleanup gracefully
    time.sleep(0.5)

    # Dispose database connections
    await async_engine.dispose()
    logger.info("Shutdown complete")


fastapi_app = FastAPI(
    title=settings.service_name,
    version="1.0.0",
    description="AI-powered resume parsing with real-time WebSocket updates",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.add_middleware(
    PerformanceMonitoringMiddleware,
    slow_threshold=2.0,
    very_slow_threshold=5.0,
)

fastapi_app.include_router(api_router, prefix="/api/v1")


@fastapi_app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "healthy",
        "websocket_path": "/ws/socket.io",
        "api_docs": "/docs",
        "health_check": "/health",
    }


@fastapi_app.get("/health", tags=["Health"])
async def health_check():
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Uptime
    uptime = time.time() - getattr(fastapi_app.state, "start_time", time.time())

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": settings.service_name,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime, 2),
        "database": {
            "status": db_status,
            "type": "PostgreSQL",
            "pgvector_enabled": settings.pgvector_enabled,
        },
        "websocket": {
            "enabled": True,
            "path": "/ws/socket.io",
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
        },
        "features": {
            "pdf_parsing": True,
            "docx_parsing": True,
            "ocr_support": True,
            "nlp_extraction": True,
            "vector_embeddings": True,
            "ai_summary": True,
            "semantic_search": True,
            "skill_search": True,
            "similar_resumes": True,
            "realtime_updates": True,
            "batch_upload": True,
            "csv_export": True,
        },
    }


# Wrap Socket.IO
app = socketio.ASGIApp(
    sio,
    other_asgi_app=fastapi_app,
    socketio_path="/ws/socket.io",
)
