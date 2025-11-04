"""Company management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (get_current_active_user, require_company_admin,
                           require_role)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.company_service import CompanyService, get_company_service

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyRead:
    """Create a new company (Admin only).

    **Authorization:**
    - Bearer <access_token> with ADMIN role

    **Request Body:**
    - name: Company name (required)
    - industry: Industry type (optional)
    - size: Company size (optional)
    - logo_url: Company logo URL (optional)
    - subscription_tier: Subscription tier (default: FREE)

    **Response:**
    - Created company with all details

    **Errors:**
    - 401: Invalid token
    - 403: Not an admin
    - 422: Invalid input data
    """
    try:
        company = await company_service.create_company(company_data)
        return company
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: str,
    current_user: User = Depends(get_current_active_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyRead:
    """Get company details.

    **Authorization:**
    - Bearer <access_token>

    **Path Parameters:**
    - company_id: Company ID

    **Response:**
    - Company details

    **Errors:**
    - 401: Invalid token
    - 404: Company not found
    """
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company


@router.put("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: str,
    update_data: CompanyUpdate,
    current_user: User = Depends(get_current_active_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyRead:
    """Update company details (Admin or company member only).

    **Authorization:**
    - Bearer <access_token>
    - User must be ADMIN or part of the company

    **Path Parameters:**
    - company_id: Company ID to update

    **Request Body:**
    - name: (optional) New company name
    - industry: (optional) New industry
    - size: (optional) New size
    - logo_url: (optional) New logo URL
    - subscription_tier: (optional) New subscription tier

    **Response:**
    - Updated company

    **Errors:**
    - 401: Invalid token
    - 403: Insufficient permissions
    - 404: Company not found
    """
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Allow ADMIN users or company members to update
    if current_user.role != UserRole.ADMIN and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own company",
        )

    try:
        updated_company = await company_service.update_company(company, update_data)
        return updated_company
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[CompanyRead])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    company_service: CompanyService = Depends(get_company_service),
) -> List[CompanyRead]:
    """List all companies.

    **Authorization:**
    - Bearer <access_token>

    **Query Parameters:**
    - skip: Number of companies to skip (default: 0)
    - limit: Maximum companies to return (default: 100, max: 1000)

    **Response:**
    - List of companies

    **Errors:**
    - 401: Invalid token
    """
    if limit > 1000:
        limit = 1000

    companies = await company_service.list_companies(skip=skip, limit=limit)
    return companies


@router.get("/{company_id}/users", response_model=List)
async def get_company_users(
    company_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    company_service: CompanyService = Depends(get_company_service),
) -> List:
    """Get all users in a company.

    **Authorization:**
    - Bearer <access_token>

    **Path Parameters:**
    - company_id: Company ID

    **Query Parameters:**
    - skip: Number of users to skip (default: 0)
    - limit: Maximum users to return (default: 100, max: 1000)

    **Response:**
    - List of users in company

    **Errors:**
    - 401: Invalid token
    - 404: Company not found
    """
    # Verify company exists
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if limit > 1000:
        limit = 1000

    users = await company_service.get_company_users(company_id, skip=skip, limit=limit)
    return users


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_service: CompanyService = Depends(get_company_service),
) -> None:
    """Delete a company (Admin only).

    **Authorization:**
    - Bearer <access_token> with ADMIN role

    **Path Parameters:**
    - company_id: Company ID to delete

    **Effects:**
    - Company deleted
    - All users removed from company

    **Response:**
    - 204 No Content on success

    **Errors:**
    - 401: Invalid token
    - 403: Not an admin
    - 404: Company not found
    """
    try:
        await company_service.delete_company(company_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
