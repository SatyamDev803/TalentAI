import uuid
from typing import Optional

from common.exceptions import ResourceNotFoundError, ValidationError
from common.logger import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.schemas.skill import SkillCreate


class SkillService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_skill(self, skill_data: SkillCreate) -> Skill:
        try:
            # Check if skill already exists
            result = await self.db.execute(
                select(Skill).where(Skill.name == skill_data.name)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValidationError(f"Skill '{skill_data.name}' already exists")

            skill = Skill(
                name=skill_data.name,
                category=skill_data.category,
            )
            self.db.add(skill)
            await self.db.commit()
            await self.db.refresh(skill)
            logger.info(f"Skill created: {skill.id}")
            return skill
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating skill: {str(e)}")
            raise

    async def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        try:
            result = await self.db.execute(
                select(Skill).where(Skill.id == uuid.UUID(skill_id))
            )
            skill = result.scalar_one_or_none()
            if not skill:
                raise ResourceNotFoundError(f"Skill {skill_id} not found")
            return skill
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching skill: {str(e)}")
            raise

    async def list_skills(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Skill], int]:
        try:
            count_result = await self.db.execute(select(func.count(Skill.id)))
            total = count_result.scalar()

            offset = (page - 1) * page_size
            query = select(Skill).offset(offset).limit(page_size)
            result = await self.db.execute(query)
            skills = result.scalars().all()

            return skills, total
        except Exception as e:
            logger.error(f"Error listing skills: {str(e)}")
            raise

    async def delete_skill(self, skill_id: str) -> bool:
        try:
            skill = await self.get_skill_by_id(skill_id)

            await self.db.delete(skill)
            await self.db.commit()
            logger.info(f"Skill deleted: {skill.id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting skill: {str(e)}")
            raise
