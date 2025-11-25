"""Services package - UPDATED"""

# Remove old imports
# from app.services.llm_client import LLMClient  # REMOVE THIS

# Keep these
from app.services.embedding_service import embedding_service
from app.services.matching_service import matching_service

# from app.services.vector_sync_service import vector_sync_service
from app.services.vector_search_service import vector_search_service
from app.services.llm_orchestrator import llm_orchestrator  # ADD THIS

__all__ = [
    "embedding_service",
    "matching_service",
    # "vector_sync_service",
    "vector_search_service",
    "llm_orchestrator",  # ADD THIS
]
