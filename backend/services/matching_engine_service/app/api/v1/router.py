from fastapi import APIRouter

from app.api.v1.endpoints import health, matching, vectors, langchain

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(matching.router, prefix="/matching", tags=["Matching"])
api_router.include_router(vectors.router, prefix="/vectors", tags=["Vectors"])
api_router.include_router(langchain.router, prefix="/langchain", tags=["LangChain"])
