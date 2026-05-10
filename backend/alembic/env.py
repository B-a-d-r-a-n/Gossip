import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config
from logging.config import fileConfig
from alembic import context
from core.config import settings
from models.base import Base
from typing import cast, Any, Dict


# Import all models so Alembic can detect them
from models import user, channel, message  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
fileConfig(cast(str, config.config_file_name))
target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    section = config.get_section(config.config_ini_section)
    connectable = async_engine_from_config(
    cast(Dict[str, Any], section),
    prefix="sqlalchemy.",
)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


run_migrations_online()
