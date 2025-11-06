from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user, require_role
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
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

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
