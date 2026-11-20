from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import text

START = datetime(2026, 12, 1, 9, 0, 0)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def seed_course(engine, course_id: uuid.UUID | None = None) -> uuid.UUID:
    course_id = course_id or new_uuid()
    payload = course_id if engine.dialect.name == "postgresql" else course_id.hex
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO acad_course (id) VALUES (:id)"), {"id": payload}
        )
    return course_id


def session_values(course_id: uuid.UUID, **overrides):
    values = {
        "id": new_uuid(),
        "org_id": new_uuid(),
        "site_id": None,
        "created_by": None,
        "deleted_at": None,
        "course_id": course_id,
        "session_no": 1,
        "label": "第 1 期",
        "start_at": START,
        "end_at": START + timedelta(hours=2),
        "room_name": "A 座 3F 多功能厅",
        "capacity": 30,
        "waitlist_capacity": 10,
        "signup_open_at": START - timedelta(days=10),
        "signup_close_at": START - timedelta(days=1),
        "require_review": True,
        "cancel_deadline_hours": 24,
        "event_id": None,
        "application_template_id": None,
        "status": "scheduled",
        "cancel_reason": None,
    }
    values.update(overrides)
    return values
