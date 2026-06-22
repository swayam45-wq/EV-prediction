"""
Alembic environment configuration for async SQLAlchemy.

Supports:
    - Offline migrations (generate SQL scripts without a live DB)
    - Online async migrations (runs against the actual DB)
    - DATABASE_URL env override (for production PostgreSQL)
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Make backend/ importable when running `alembic` from backend/ ──
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Import our metadata so Alembic can detect model changes ──
from models.database import Base   # noqa: E402  (must come after sys.path fix)
from config import settings        # noqa: E402

# ── Alembic Config object ──────────────────────────────────
config = context.config

# Override sqlalchemy.url from env variable if provided
db_url = settings.database_url or "sqlite+aiosqlite:///./ev_charging.db"
config.set_main_option("sqlalchemy.url", db_url)

# ── Python logging setup ───────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata for autogenerate ──────────────────────
target_metadata = Base.metadata


# ── OFFLINE mode ───────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Emit SQL to stdout instead of running against a live DB.
    Useful for generating migration scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,   # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


# ── ONLINE mode (async) ────────────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,   # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in online mode using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
