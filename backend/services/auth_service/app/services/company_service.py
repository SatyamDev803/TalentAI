"""Company service business logic."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate


class CompanyService:
    """Company service with business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_company(
        self,
        company_data: CompanyCreate,
    ) -> Company:
        """Create a new company.

        Args:
            company_data: Company creation data

        Returns:
            Created company
        """
        company = Company(
            id=str(uuid4()),
            name=company_data.name,
            industry=company_data.industry,
            size=company_data.size,
            logo_url=company_data.logo_url,
            subscription_tier=company_data.subscription_tier,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)

        return company

    async def get_company_by_id(self, company_id: str) -> Optional[Company]:
        """Get company by ID.

        Args:
            company_id: Company ID

        Returns:
            Company if found, None otherwise
        """
        stmt = select(Company).where(Company.id == company_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get company by name.

        Args:
            name: Company name

        Returns:
            Company if found, None otherwise
        """
        stmt = select(Company).where(Company.name == name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_company(
        self,
        company: Company,
        update_data: CompanyUpdate,
    ) -> Company:
        """Update company information.

        Args:
            company: Company to update
            update_data: Update data

        Returns:
            Updated company
        """
        if update_data.name:
            company.name = update_data.name

        if update_data.industry:
            company.industry = update_data.industry

        if update_data.size:
            company.size = update_data.size

        if update_data.logo_url:
            company.logo_url = update_data.logo_url

        if update_data.subscription_tier:
            company.subscription_tier = update_data.subscription_tier

        company.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(company)

        return company

    async def list_companies(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Company]:
        """List all companies.

        Args:
            skip: Number of companies to skip
            limit: Maximum companies to return

        Returns:
            List of companies
        """
        stmt = select(Company).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_company_users(
        self,
        company_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """Get all users in a company.

        Args:
            company_id: Company ID
            skip: Number of users to skip
            limit: Maximum users to return

        Returns:
            List of users in company
        """
        stmt = (
            select(User).where(User.company_id == company_id).offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def add_user_to_company(
        self,
        user: User,
        company_id: str,
    ) -> User:
        """Add user to a company.

        Args:
            user: User to add to company
            company_id: Company ID

        Returns:
            Updated user

        Raises:
            ValueError: If company doesn't exist
        """
        # Verify company exists
        company = await self.get_company_by_id(company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # Update user's company
        user.company_id = company_id
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def remove_user_from_company(
        self,
        user: User,
    ) -> User:
        """Remove user from their company.

        Args:
            user: User to remove from company

        Returns:
            Updated user
        """
        user.company_id = None
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_company(self, company_id: str) -> bool:
        """Delete a company.

        Also removes all users from the company.

        Args:
            company_id: Company ID to delete

        Returns:
            True if successful

        Raises:
            ValueError: If company not found
        """
        company = await self.get_company_by_id(company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # Remove all users from company
        stmt = select(User).where(User.company_id == company_id)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        for user in users:
            user.company_id = None
            user.updated_at = datetime.now(timezone.utc)

        # Delete company
        await self.db.delete(company)
        await self.db.commit()

        return True


async def get_company_service(db: AsyncSession = Depends(get_db)) -> CompanyService:
    """Dependency to get company service.

    Args:
        db: Database session from FastAPI dependency injection

    Returns:
        CompanyService instance
    """
    return CompanyService(db)
