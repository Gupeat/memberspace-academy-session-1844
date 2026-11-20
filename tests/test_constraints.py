from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import insert as sa_insert, select
from sqlalchemy.exc import DataError, IntegrityError

from app.academy.models import AcadCourseSession
from tests.helpers import START, new_uuid, seed_course, session_values

TABLE = AcadCourseSession.__table__


def insert_row(engine, values):
    with engine.begin() as connection:
        connection.execute(sa_insert(TABLE).values(**values))


def expect_rejected(engine, values):
    with pytest.raises((IntegrityError, DataError)):
        insert_row(engine, values)


def test_end_at_must_be_after_start_at(engine):
    course = seed_course(engine)
    expect_rejected(
        engine,
        session_values(course, start_at=START, end_at=START),
    )
    expect_rejected(
        engine,
        session_values(course, start_at=START, end_at=START - timedelta(minutes=1)),
    )


def test_signup_close_must_not_be_after_start(engine):
    course = seed_course(engine)
    expect_rejected(
        engine,
        session_values(course, signup_close_at=START + timedelta(seconds=1)),
    )
    insert_row(engine, session_values(course, signup_close_at=START))


def test_signup_open_must_be_before_close(engine):
    course = seed_course(engine)
    expect_rejected(
        engine,
        session_values(course, signup_open_at=START - timedelta(days=1), signup_close_at=START - timedelta(days=1)),
    )


def test_capacity_range(engine):
    course = seed_course(engine)
    for capacity in (0, 501):
        expect_rejected(engine, session_values(course, capacity=capacity))
    insert_row(engine, session_values(course, capacity=1))
    insert_row(engine, session_values(course, capacity=500, session_no=2))


def test_waitlist_range(engine):
    course = seed_course(engine)
    for waitlist in (-1, 101):
        expect_rejected(engine, session_values(course, waitlist_capacity=waitlist))
    insert_row(engine, session_values(course, waitlist_capacity=0))
    insert_row(engine, session_values(course, waitlist_capacity=100, session_no=2))


def test_session_no_positive(engine):
    course = seed_course(engine)
    expect_rejected(engine, session_values(course, session_no=0))


def test_status_vocabulary(engine):
    course = seed_course(engine)
    expect_rejected(engine, session_values(course, status="draft"))
    insert_row(engine, session_values(course, status="signup_open"))


def test_label_length_and_blank(engine):
    course = seed_course(engine)
    expect_rejected(engine, session_values(course, label="x" * 21))
    expect_rejected(engine, session_values(course, label="   "))
    insert_row(engine, session_values(course, label="第 1 期"))


def test_room_name_length_and_blank(engine):
    course = seed_course(engine)
    expect_rejected(engine, session_values(course, room_name="x" * 31))
    expect_rejected(engine, session_values(course, room_name="   "))
    insert_row(engine, session_values(course, room_name="A 座 3F 多功能厅"))


def test_cancel_reason_length(engine):
    course = seed_course(engine)
    expect_rejected(engine, session_values(course, cancel_reason="x" * 201))
    insert_row(engine, session_values(course, cancel_reason="场地检修", status="cancelled"))


def test_duplicate_session_no_same_course_rejected(engine):
    course = seed_course(engine)
    insert_row(engine, session_values(course, session_no=1))
    expect_rejected(engine, session_values(course, session_no=1))


def test_same_session_no_allowed_for_different_courses(engine):
    first = seed_course(engine)
    second = seed_course(engine)
    insert_row(engine, session_values(first, session_no=1))
    insert_row(engine, session_values(second, session_no=1))


def test_event_id_unique_but_nullable(engine):
    course = seed_course(engine)
    event = new_uuid()
    insert_row(engine, session_values(course, session_no=1, event_id=event))
    expect_rejected(engine, session_values(course, session_no=2, event_id=event))
    insert_row(engine, session_values(course, session_no=2, event_id=None))
    insert_row(engine, session_values(course, session_no=3, event_id=None))


def test_defaults(engine):
    course = seed_course(engine)
    values = session_values(course)
    for key in ("waitlist_capacity", "require_review", "cancel_deadline_hours", "status"):
        values.pop(key)
    insert_row(engine, values)
    with engine.connect() as connection:
        row = connection.execute(
            select(
                TABLE.c.waitlist_capacity,
                TABLE.c.require_review,
                TABLE.c.cancel_deadline_hours,
                TABLE.c.status,
            )
        ).one()
    assert row.waitlist_capacity == 0
    assert row.require_review is False
    assert row.cancel_deadline_hours == 24
    assert row.status == "scheduled"


def test_orm_validators_reject_bad_values():
    values = session_values(uuid.uuid4())
    values.pop("id")
    values["label"] = "x" * 21
    with pytest.raises(ValueError):
        AcadCourseSession(**values)
