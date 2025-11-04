# ruff: noqa: E402
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Get absolute paths
current_file = Path(__file__).resolve()  # alembic/env.py
alembic_dir = current_file.parent  # alembic/
auth_service_dir = alembic_dir.parent  # auth_service/
services_dir = auth_service_dir.parent  # services/
backend_dir = services_dir.parent  # backend/
project_root = backend_dir.parent  # talentai-pro/
shared_dir = backend_dir / "shared"  # backend/shared/

for path_to_add in [str(shared_dir), str(auth_service_dir)]:
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

from common.config import BaseConfig
from app.db.base import Base
from app.models import user, company  # noqa: F401
from app.models.job import Job
from app.models.application import Application
from app.models.skill import Skill
from app.models.category import Category


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from shared config."""
    settings = BaseConfig()
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
