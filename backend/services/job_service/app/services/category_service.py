import uuid
from typing import Optional

from common.exceptions import ResourceNotFoundError, ValidationError
from common.logging import get_logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate

logger = get_logger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, category_data: CategoryCreate) -> Category:
        try:
            # Check if category already exists
            result = await self.db.execute(
                select(Category).where(Category.name == category_data.name)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValidationError(f"Category '{category_data.name}' already exists")

            category = Category(
                name=category_data.name,
                description=category_data.description,
            )
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)
            logger.info(f"Category created: {category.id}")
            return category
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating category: {str(e)}")
            raise

    async def get_category_by_id(self, category_id: str) -> Optional[Category]:
        try:
            result = await self.db.execute(
                select(Category).where(Category.id == uuid.UUID(category_id))
            )
            category = result.scalar_one_or_none()
            if not category:
                raise ResourceNotFoundError(f"Category {category_id} not found")
            return category
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching category: {str(e)}")
            raise

    async def list_categories(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Category], int]:
        try:
            count_result = await self.db.execute(select(func.count(Category.id)))
            total = count_result.scalar()

            offset = (page - 1) * page_size
            query = select(Category).offset(offset).limit(page_size)
            result = await self.db.execute(query)
            categories = result.scalars().all()

            return categories, total
        except Exception as e:
            logger.error(f"Error listing categories: {str(e)}")
            raise
