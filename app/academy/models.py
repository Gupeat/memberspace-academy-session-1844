"""SQLAlchemy model for one offering of an academy course."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.academy import constants
from app.db import Base, SystemFieldsMixin

# Integration stub for the sibling course table owned by #1839. The real table
# has many more columns; this metadata entry exists only so SQLAlchemy can
# resolve the foreign key. alembic/env.py excludes acad_course from autogenerate.
acad_course = Table(
    "acad_course",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    info={"external_dependency": True},
)


class AcadCourseSession(SystemFieldsMixin, Base):
    __tablename__ = "acad_course_session"

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("acad_course.id", name="fk_acad_course_session_course_id"), nullable=False
    )
    session_no: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    room_name: Mapped[str] = mapped_column(String(30), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    waitlist_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    signup_open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signup_close_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    require_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    cancel_deadline_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("24")
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    application_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'scheduled'")
    )
    cancel_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    __table_args__ = (
        CheckConstraint("end_at > start_at", name="time_order"),
        CheckConstraint("signup_open_at < signup_close_at", name="signup_window"),
        CheckConstraint("signup_close_at <= start_at", name="signup_before_start"),
        CheckConstraint("capacity BETWEEN 1 AND 500", name="capacity_range"),
        CheckConstraint("waitlist_capacity BETWEEN 0 AND 100", name="waitlist_range"),
        CheckConstraint("session_no >= 1", name="session_no_positive"),
        CheckConstraint("cancel_deadline_hours >= 0", name="cancel_deadline_nonnegative"),
        CheckConstraint(
            "status IN ('scheduled','signup_open','signup_closed','in_progress','finished','cancelled')",
            name="status_enum",
        ),
        CheckConstraint("length(label) <= 20", name="label_length"),
        CheckConstraint("length(trim(label)) > 0", name="label_not_blank"),
        CheckConstraint("length(room_name) <= 30", name="room_name_length"),
        CheckConstraint("length(trim(room_name)) > 0", name="room_name_not_blank"),
        CheckConstraint(
            "cancel_reason IS NULL OR length(cancel_reason) <= 200",
            name="cancel_reason_length",
        ),
        UniqueConstraint(
            "course_id",
            "session_no",
            name="uq_acad_course_session_course_session_no",
        ),
        UniqueConstraint("event_id", name="uq_acad_course_session_event_id"),
        Index("ix_acad_course_session_org_start", "org_id", "start_at"),
        Index("ix_acad_course_session_course_start", "course_id", "start_at"),
    )

    @validates("label")
    def _validate_label(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("label is required")
        if len(value) > constants.LABEL_MAX_CHARS:
            raise ValueError("label must be at most 20 characters")
        return value

    @validates("room_name")
    def _validate_room_name(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("room_name is required")
        if len(value) > constants.ROOM_NAME_MAX_CHARS:
            raise ValueError("room_name must be at most 30 characters")
        return value

    @validates("cancel_reason")
    def _validate_cancel_reason(self, _key: str, value: str | None) -> str | None:
        if value is not None and len(value) > constants.CANCEL_REASON_MAX_CHARS:
            raise ValueError("cancel_reason must be at most 200 characters")
        return value

    @validates("session_no")
    def _validate_session_no(self, _key: str, value: int) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError("session_no must be an integer >= 1")
        return value

    @validates("capacity", "waitlist_capacity")
    def _validate_capacity(self, key: str, value: int) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{key} must be an integer")
        lower, upper = (
            (constants.CAPACITY_MIN, constants.CAPACITY_MAX)
            if key == "capacity"
            else (constants.WAITLIST_MIN, constants.WAITLIST_MAX)
        )
        if value < lower or value > upper:
            raise ValueError(f"{key} out of range")
        return value

    @validates("status")
    def _validate_status(self, _key: str, value: str) -> str:
        if value not in constants.SESSION_STATUSES:
            raise ValueError("status is not in the closed vocabulary")
        return value

    @validates("start_at", "end_at", "signup_open_at", "signup_close_at")
    def _validate_time(self, key: str, value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(f"{key} must be a datetime")
        return value

    def soft_delete(self) -> "AcadCourseSession":
        self.deleted_at = datetime.now(timezone.utc)
        return self

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"AcadCourseSession(id={self.id!r}, course_id={self.course_id!r}, session_no={self.session_no!r})"
