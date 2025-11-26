from typing import Optional

from app.utils.chroma_manager import ChromaManager
from common.logging import get_logger
from app.utils.chroma_manager import chroma_manager
from app.services.embedding_service import embedding_service
from app.services.vector_search_service import vector_search_service
from app.services.llm_orchestrator import llm_orchestrator


logger = get_logger(__name__)

# Global instances
_chroma_manager: Optional[ChromaManager] = None
_services_initialized = False


def set_chroma_manager(manager: ChromaManager) -> None:
    global _chroma_manager
    _chroma_manager = manager
    logger.info("Chroma manager registered in service registry")


def get_chroma_manager() -> Optional[ChromaManager]:
    if _chroma_manager is None:
        logger.warning("Chroma manager not initialized")
    return _chroma_manager


def is_chroma_ready() -> bool:
    return _chroma_manager is not None


def initialize_all_services():
    global _services_initialized

    if _services_initialized:
        logger.info("Services already initialized")
        return

    try:
        # Initialize ChromaDB
        if _chroma_manager is None:

            set_chroma_manager(chroma_manager)

        llm_orchestrator._ensure_initialized()

        _services_initialized = True
        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


def get_service_status() -> dict:
    return {
        "chroma_ready": is_chroma_ready(),
        "services_initialized": _services_initialized,
    }
