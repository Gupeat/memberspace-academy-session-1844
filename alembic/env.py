"""Alembic environment for the academy database."""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.academy import models  # noqa: F401
from app.db import Base, create_db_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DATABASE_URL = os.environ.get("ACADEMY_DB_URL") or config.get_main_option("sqlalchemy.url")


def include_object(object_, name, type_, reflected, compare_to):
    """Keep the externally-owned acad_course dependency out of autogenerate.

    #1844 owns only acad_course_session. The migration creates a minimal
    acad_course stub when the sibling course table is absent, so Alembic
    must ignore that stub during alembic check rather than proposing to
    drop a table it does not own.
    """
    if type_ == "table" and name == "acad_course":
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=DATABASE_URL.startswith("sqlite"),
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    if DATABASE_URL.startswith("sqlite"):
        connectable = create_db_engine(DATABASE_URL)
    else:
        section = config.get_section(config.config_ini_section, {})
        section["sqlalchemy.url"] = DATABASE_URL
        connectable = engine_from_config(
            section, prefix="sqlalchemy.", poolclass=pool.NullPool
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=DATABASE_URL.startswith("sqlite"),
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
