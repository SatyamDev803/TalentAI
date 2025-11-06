from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4, UUID

from common.logger import logger
from common.redis_client import redis_client
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AuthConfig
from app.core.security import (
    create_tokens,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserUpdate

settings = AuthConfig()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(
        self,
        user_data: UserCreate,
        company_id: Optional[str] = None,
    ) -> Tuple[User, Token]:

        stmt = select(User).where(User.email == user_data.email)
        result = await self.db.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            raise ValueError(f"Email {user_data.email} already registered")

        user = User(
            id=str(uuid4()),
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            company_id=company_id,
            is_active=True,
            is_verified=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        tokens = create_tokens(
            str(user.id),
            role=user.role,
            email=user.email,
            company_id=str(user.company_id) if user.company_id else None,
        )

        refresh_payload = decode_token(tokens["refresh_token"])
        await redis_client.store_refresh_token(
            refresh_payload["jti"],
            str(user.id),
            refresh_payload["exp"] - int(datetime.now(timezone.utc).timestamp()),
        )

        return user, Token(**tokens)

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[User, Token]:

        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        tokens = create_tokens(
            str(user.id),
            role=user.role,
            email=user.email,
            company_id=str(user.company_id) if user.company_id else None,
        )

        refresh_payload = decode_token(tokens["refresh_token"])
        await redis_client.store_refresh_token(
            refresh_payload["jti"],
            str(user.id),
            refresh_payload["exp"] - int(datetime.now(timezone.utc).timestamp()),
        )

        return user, Token(**tokens)

    async def refresh_access_token(self, user: User) -> Token:
        tokens = create_tokens(
            str(user.id),
            role=user.role,
            email=user.email,
            company_id=str(user.company_id) if user.company_id else None,
        )

        refresh_payload = decode_token(tokens["refresh_token"])
        await redis_client.store_refresh_token(
            refresh_payload["jti"],
            str(user.id),
            refresh_payload["exp"] - int(datetime.now(timezone.utc).timestamp()),
        )

        return Token(**tokens)

    async def logout_user(
        self,
        user: User,
        access_jti: str,
        refresh_jti: str,
    ) -> bool:

        access_exp = settings.access_token_expire_minutes * 60
        refresh_exp = settings.refresh_token_expire_days * 86400

        await redis_client.blacklist_token(access_jti, access_exp)
        await redis_client.blacklist_token(refresh_jti, refresh_exp)
        await redis_client.revoke_refresh_token(refresh_jti)

        return True

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return None

        stmt = select(User).where(User.id == user_uuid)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_user_profile(
        self,
        user: User,
        update_data: UserUpdate,
    ) -> User:

        if update_data.full_name:
            user.full_name = update_data.full_name

        if update_data.role:
            user.role = update_data.role

        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> User:

        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        # Revoke all tokens on password change
        await redis_client.revoke_all_user_tokens(str(user.id))

        return user

    async def verify_user_email(self, user: User) -> User:
        user.is_verified = True
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def deactivate_user(self, user: User) -> User:
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        # Revoke all tokens on deactivation
        await redis_client.revoke_all_user_tokens(str(user.id))

        return user

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:

        stmt = select(User).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_company_users(
        self,
        company_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:

        stmt = (
            select(User).where(User.company_id == company_id).offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)
