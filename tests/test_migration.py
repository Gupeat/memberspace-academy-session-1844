from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, text

from app.academy.models import AcadCourseSession
from app.db import create_db_engine
from tests.helpers import new_uuid, seed_course, session_values

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_COLUMNS = {
    "id",
    "org_id",
    "site_id",
    "created_at",
    "created_by",
    "updated_at",
    "deleted_at",
    "course_id",
    "session_no",
    "label",
    "start_at",
    "end_at",
    "room_name",
    "capacity",
    "waitlist_capacity",
    "signup_open_at",
    "signup_close_at",
    "require_review",
    "cancel_deadline_hours",
    "event_id",
    "application_template_id",
    "status",
    "cancel_reason",
}


def test_schema_columns_and_defaults(engine):
    inspector = inspect(engine)
    assert "acad_course_session" in inspector.get_table_names()
    columns = {column["name"]: column for column in inspector.get_columns("acad_course_session")}
    assert set(columns) == EXPECTED_COLUMNS
    assert len(columns) == 23
    assert columns["course_id"]["nullable"] is False
    assert columns["event_id"]["nullable"] is True
    assert columns["application_template_id"]["nullable"] is True
    assert columns["waitlist_capacity"]["default"] is not None
    assert columns["require_review"]["default"] is not None
    assert columns["cancel_deadline_hours"]["default"] is not None
    assert columns["status"]["default"] is not None


def test_unique_constraints_and_indexes(engine):
    inspector = inspect(engine)
    uniques = {
        tuple(constraint["column_names"]): constraint
        for constraint in inspector.get_unique_constraints("acad_course_session")
    }
    assert ("course_id", "session_no") in uniques
    assert ("event_id",) in uniques
    indexes = {index["name"] for index in inspector.get_indexes("acad_course_session")}
    assert "ix_acad_course_session_org_start" in indexes
    assert "ix_acad_course_session_course_start" in indexes


def test_upgrade_downgrade_cycle(engine, alembic_config):
    assert "acad_course_session" in inspect(engine).get_table_names()
    command.downgrade(alembic_config, "base")
    assert "acad_course_session" not in inspect(engine).get_table_names()
    assert "acad_course" in inspect(engine).get_table_names()
    command.upgrade(alembic_config, "head")
    assert "acad_course_session" in inspect(engine).get_table_names()


def test_alembic_check_has_no_drift(engine, database_url):
    env = os.environ.copy()
    env["ACADEMY_DB_URL"] = database_url
    completed = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(REPO_ROOT / "alembic.ini"), "check"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "No new upgrade operations detected." in output


def test_seeded_upgrade_downgrade_cycle(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "seeded.db")
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    monkeypatch.setenv("ACADEMY_DB_URL", url)
    engine = create_db_engine(url)

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE acad_course (id UUID PRIMARY KEY)"))
        seed_id = new_uuid()
        connection.execute(
            text("INSERT INTO acad_course (id) VALUES (:id)"), {"id": seed_id.hex}
        )

    command.upgrade(config, "head")
    with engine.begin() as connection:
        connection.execute(
            AcadCourseSession.__table__.insert().values(**session_values(seed_id))
        )

    command.downgrade(config, "base")
    assert "acad_course_session" not in inspect(engine).get_table_names()
    assert "acad_course" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM acad_course")).scalar_one() == 1

    command.upgrade(config, "head")
    assert "acad_course_session" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM acad_course")).scalar_one() == 1
    engine.dispose()
