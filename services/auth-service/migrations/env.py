"""Alembic env — async + reads database url from $DATABASE_URL."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from auth_service.models import RefreshToken, User  # noqa: F401
from ford_shared.db.base import Base

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata
DB_SCHEMA = os.environ.get("DB_SCHEMA", "auth")


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and obj.schema and obj.schema != DB_SCHEMA:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        version_table_schema=DB_SCHEMA,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    connection.execute(__import__("sqlalchemy").text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=DB_SCHEMA,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
