from common.exceptions import ValidationError
from common.logger import logger
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import (get_category_service, get_current_active_user,
                           require_role)
from app.schemas.category import (CategoryCreate, CategoryListResponse,
                                  CategoryRead)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=CategoryListResponse, status_code=status.HTTP_200_OK)
async def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryListResponse:
    """List all categories"""
    try:
        categories, total = await category_service.list_categories(page, page_size)
        return CategoryListResponse(
            total=total,
            categories=categories,
        )
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list categories",
        )


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(require_role("ADMIN")),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Create a new category (Admin only)"""
    try:
        category = await category_service.create_category(category_data)
        return category
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category",
        )
