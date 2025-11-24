from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import signal
import asyncio
from pathlib import Path

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
from app.services.cache_service import cache_service

setup_logging(
    service_name="matching-engine-service",
    log_level=settings.log_level,
    log_format="json" if settings.is_production else "text",
    enable_file_logging=not settings.is_production,
)
logger = get_logger(__name__)

_shutdown_event = None


async def warm_popular_caches():
    try:
        await asyncio.sleep(5)

        await cache_service.get_cache_stats()

        logger.info("Cache warming complete")
    except Exception as e:
        logger.error(f"Cache warming error: {e}")


def _setup_signal_handlers():

    def graceful_shutdown_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if _shutdown_event:
            _shutdown_event.set()

    # Override Ray's signal handlers
    signal.signal(signal.SIGTERM, graceful_shutdown_handler)
    signal.signal(signal.SIGINT, graceful_shutdown_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _shutdown_event
    logger = get_logger(__name__)
    logger.info("Starting Matching Engine Service...")

    _setup_signal_handlers()

    try:
        # Initialize Redis
        logger.info("Initializing Redis...")
        await init_redis()
        logger.info("Redis initialized")

        # Initialize Database
        logger.info("Initializing PostgreSQL Database...")
        await init_db()
        logger.info("Database initialized")

        # Initialize Ray
        logger.info("Initializing Ray...")
        RayManager.init_ray()
        logger.info(f"Ray initialized with {settings.ray_num_cpus} CPUs")

        # Initialize Chroma
        logger.info("Initializing ChromaDB...")
        try:
            chroma_manager = ChromaManager()
            set_chroma_manager(chroma_manager)
            logger.info("ChromaDB initialized and registered")
            logger.info(f"Chroma persist directory: {settings.chroma_persist_dir}")
            logger.info(f"Embedding model: {settings.sentence_transformer_model}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

        try:
            logger.info("Warming cache...")
            # Pre load frequently accessed data
            # This runs in background, doesn't block startup
            asyncio.create_task(warm_popular_caches())
        except Exception as e:
            logger.warning(f"Cache warming failed (non-critical): {e}")

        logger.info("All services initialized successfully!")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    try:
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        # Handle cancellation gracefully
        logger.info("Shutdown signal received")
    finally:
        # Shutdown
        logger.info("Shutting down Matching Engine Service...")

        # Shutdown Ray
        try:
            logger.info("Shutting down Ray...")
            try:
                RayManager.shutdown_ray()
            except SystemExit:
                logger.debug("Ray shutdown complete (SystemExit suppressed)")
            logger.info("Ray shutdown complete")
        except Exception as e:
            logger.error(f"Error during Ray shutdown: {e}")

        try:
            # Close Database
            logger.info("Closing database connection...")
            await close_db()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

        try:
            # Close Redis
            logger.info("Closing Redis connection...")
            await close_redis()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")

        logger.info("Shutdown complete!")


app = FastAPI(
    title=settings.SERVICE_NAME,
    description="AI-powered candidate-job matching with Ray",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
