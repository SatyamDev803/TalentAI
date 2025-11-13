"""Main application entry point with Socket.IO WebSocket support."""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import async_engine, get_db
from app.middleware.performance import PerformanceMonitoringMiddleware
from app.core.websocket import sio

# Find and load root .env
root_env = Path(__file__).resolve().parents[4] / ".env"
if root_env.exists():
    print(f"✅ Found .env at: {root_env}")
    print(f"🔧 Loading .env from: {root_env}")
    load_dotenv(root_env, override=True)
else:
    print(f"⚠️  .env not found at: {root_env}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events with model preloading."""
    # Startup
    print("\n" + "=" * 60)
    print("🚀 RESUME PARSER SERVICE STARTING")
    setup_logging(log_level=settings.log_level or "INFO")
    print("=" * 60)

    # DEBUG: Print JWT config
    print(f"✅ JWT_SECRET from config: {settings.jwt_secret[:20]}...")
    print(f"✅ JWT_SECRET from env: {os.getenv('JWT_SECRET', 'NOT FOUND')[:20]}...")
    print(f"✅ JWT_ALGORITHM: {settings.jwt_algorithm}")

    # ✅ PRELOAD EMBEDDING MODEL AT STARTUP
    from app.utils.embedding_generator import preload_model

    preload_model()

    # Track startup time
    app.state.start_time = time.time()

    print("=" * 60 + "\n")

    yield

    # Shutdown - cleanup ML resources
    try:
        from joblib.externals.loky import get_reusable_executor

        executor = get_reusable_executor()
        executor.shutdown(wait=True, kill_workers=False)
    except Exception:
        pass

    # Give threads time to cleanup cleanly (500ms)
    time.sleep(0.5)

    # Dispose database engine
    await async_engine.dispose()


# ═══════════════════════════════════════════════════════════
# Create FastAPI app (DON'T wrap yet!)
# ═══════════════════════════════════════════════════════════

fastapi_app = FastAPI(
    title="Resume Parser Service",
    version="2.0.0",
    description="AI-powered resume parsing with real-time WebSocket updates",
    lifespan=lifespan,
)

# CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance monitoring
fastapi_app.add_middleware(PerformanceMonitoringMiddleware)

# Include routers
fastapi_app.include_router(api_router, prefix="/api/v1")


# ═══════════════════════════════════════════════════════════
# Define routes on FastAPI app BEFORE wrapping
# ═══════════════════════════════════════════════════════════


@fastapi_app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Resume Parser Service",
        "version": "2.0.0",
        "status": "running",
        "websocket": "/ws/socket.io",
        "docs": "/docs",
    }


@fastapi_app.get("/health", tags=["health"])
async def health_check():
    """Comprehensive health check with system metrics."""
    import psutil

    # Check database
    try:
        async with get_db() as db:
            await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Calculate uptime
    uptime = time.time() - getattr(fastapi_app.state, "start_time", time.time())

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "Resume Parser Service",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime, 2),
        "database": {"status": db_status, "connection": "PostgreSQL"},
        "websocket": {"enabled": True, "path": "/ws/socket.io"},
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
            "ocr": True,
            "nlp_extraction": True,
            "vector_embeddings": True,
            "ai_summary": True,
            "semantic_search": True,
            "skill_search": True,
            "similar_resumes": True,
            "realtime_updates": True,
        },
    }


# ═══════════════════════════════════════════════════════════
# NOW wrap FastAPI with Socket.IO (LAST STEP!)
# ═══════════════════════════════════════════════════════════

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="/ws/socket.io")

# Note: 'app' is now the Socket.IO wrapped ASGI app
# This is what Uvicorn will run
