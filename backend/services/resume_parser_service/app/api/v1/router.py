from fastapi import APIRouter

from app.api.v1.endpoints import auth_proxy, health, resume, search

api_router = APIRouter()

# Include endpoints
api_router.include_router(auth_proxy.router, prefix="/auth", tags=["auth"])
api_router.include_router(resume.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
