from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import signal
import asyncio
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.logging import setup_logging, get_logger
from common.redis_client import init_redis, close_redis
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db, close_db
from app.utils.ray_manager import RayManager
from app.utils.chroma_manager import ChromaManager
from app.services.service_registry import set_chroma_manager
from app.middleware.request_logger import RequestLoggingMiddleware
from app.core.cache import cache_service

setup_logging(
    service_name="matching-engine-service",
    log_level=settings.log_level,
    log_format="json" if settings.is_production else "text",
    enable_file_logging=not settings.is_production,
)
logger = get_logger(__name__)

_shutdown_event: Optional[asyncio.Event] = None


async def warm_popular_caches():
    try:
        await asyncio.sleep(2)

        stats = await cache_service.get_detailed_stats()
        logger.info(f"Cache warming initiated: {stats}")

        logger.info("Cache warming complete")
    except Exception as e:
        logger.error(f"Cache warming error (non-critical): {e}", exc_info=True)


def _setup_signal_handlers():
    def graceful_shutdown_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if _shutdown_event and not _shutdown_event.is_set():
            _shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGTERM, graceful_shutdown_handler)
    signal.signal(signal.SIGINT, graceful_shutdown_handler)
    logger.debug("Signal handlers registered")


@asynccontextmanager
async def lifespan(app: FastAPI):

    global _shutdown_event
    _shutdown_event = asyncio.Event()

    logger.info("Starting Matching Engine Service")
    logger.info(
        f"Environment: {'Production' if settings.is_production else 'Development'}"
    )
    logger.info(f"Service: {settings.SERVICE_NAME}")
    logger.info(f"Port: {settings.PORT}")

    # Setup signal handlers
    _setup_signal_handlers()

    # Track initialization state for cleanup
    redis_initialized = False
    db_initialized = False
    ray_initialized = False
    chroma_initialized = False

    try:
        # Initialize Redis
        logger.info("Initializing Redis...")
        await init_redis()
        redis_initialized = True
        logger.info(f"Redis initialized (host: {settings.redis_host})")

        # Initialize PostgreSQL Database
        logger.info("Initializing PostgreSQL Database...")
        await init_db()
        db_initialized = True
        logger.info(
            f"Database initialized (URL: {settings.database_url_matching[:30]}...)"
        )

        # Initialize Ray
        logger.info("Initializing Ray cluster...")
        RayManager.init_ray()
        ray_initialized = True
        logger.info(
            f"Ray initialized ({settings.ray_num_cpus} CPUs, dashboard: {settings.ray_dashboard_port})"
        )

        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        try:
            chroma_manager = ChromaManager()
            set_chroma_manager(chroma_manager)
            chroma_initialized = True
            logger.info("ChromaDB initialized")
            logger.info(f"  - Persist directory: {settings.chroma_persist_dir}")
            logger.info(f"  - Embedding model: {settings.sentence_transformer_model}")
            logger.info(f"  - Embedding dimension: {settings.embedding_dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}", exc_info=True)
            raise

        # Start Background Tasks
        try:
            logger.info("Starting background tasks...")
            asyncio.create_task(warm_popular_caches())
            logger.info("Background tasks started")
        except Exception as e:
            logger.warning(f"Background task initialization failed (non-critical): {e}")

        logger.info("All services initialized successfully!")
        logger.info(f"Service ready at http://0.0.0.0:{settings.PORT}")
        logger.info(f"API docs available at http://0.0.0.0:{settings.PORT}/docs")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)

        # Cleanup any partially initialized services
        if ray_initialized:
            try:
                RayManager.shutdown_ray()
            except Exception:
                pass
        if db_initialized:
            try:
                await close_db()
            except Exception:
                pass
        if redis_initialized:
            try:
                await close_redis()
            except Exception:
                pass

        raise

    try:
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Shutdown signal received (Ctrl+C or SIGTERM)")
    finally:
        logger.info("Shutting down Matching Engine Service...")

        if ray_initialized:
            try:
                logger.info("Shutting down Ray cluster...")
                RayManager.shutdown_ray()
                logger.info("Ray shutdown complete")
            except SystemExit:
                logger.debug("Ray shutdown complete (SystemExit suppressed)")
            except Exception as e:
                logger.error(f"Error during Ray shutdown: {e}", exc_info=True)

        if db_initialized:
            try:
                logger.info("Closing database connections...")
                await close_db()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}", exc_info=True)

        if redis_initialized:
            try:
                logger.info("Closing Redis connections...")
                await close_redis()
                logger.info("Redis connections closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}", exc_info=True)

        logger.info("Shutdown complete - Service stopped cleanly")


app = FastAPI(
    title=settings.SERVICE_NAME,
    description="AI candidate-job matching engine with Ray distributed computing, "
    "ChromaDB vector search, and LLM-based analysis",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
    debug=not settings.is_production,
)

app.add_middleware(RequestLoggingMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
