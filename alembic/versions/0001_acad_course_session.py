"""Create acad_course_session table.

Revision ID: 0001_acad_course_session
Revises:
Create Date: 2026-11-20
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_acad_course_session"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Dependency owned by the sibling course task (#1839). The IF NOT EXISTS
    # stub keeps an empty database upgradeable while remaining a no-op when the
    # real table is already present.
    op.execute(sa.text("CREATE TABLE IF NOT EXISTS acad_course (id UUID PRIMARY KEY)"))

    op.create_table(
        "acad_course_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("session_no", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=20), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("room_name", sa.String(length=30), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "waitlist_capacity", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("signup_open_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signup_close_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "require_review", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "cancel_deadline_hours", sa.Integer(), server_default=sa.text("24"), nullable=False
        ),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column("application_template_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'scheduled'"), nullable=False
        ),
        sa.Column("cancel_reason", sa.String(length=200), nullable=True),
        sa.CheckConstraint("end_at > start_at", name=op.f("ck_acad_course_session_time_order")),
        sa.CheckConstraint(
            "signup_open_at < signup_close_at",
            name=op.f("ck_acad_course_session_signup_window"),
        ),
        sa.CheckConstraint(
            "signup_close_at <= start_at",
            name=op.f("ck_acad_course_session_signup_before_start"),
        ),
        sa.CheckConstraint(
            "capacity BETWEEN 1 AND 500",
            name=op.f("ck_acad_course_session_capacity_range"),
        ),
        sa.CheckConstraint(
            "waitlist_capacity BETWEEN 0 AND 100",
            name=op.f("ck_acad_course_session_waitlist_range"),
        ),
        sa.CheckConstraint(
            "session_no >= 1", name=op.f("ck_acad_course_session_session_no_positive")
        ),
        sa.CheckConstraint(
            "cancel_deadline_hours >= 0",
            name=op.f("ck_acad_course_session_cancel_deadline_nonnegative"),
        ),
        sa.CheckConstraint(
            "status IN ('scheduled','signup_open','signup_closed','in_progress','finished','cancelled')",
            name=op.f("ck_acad_course_session_status_enum"),
        ),
        sa.CheckConstraint(
            "length(label) <= 20", name=op.f("ck_acad_course_session_label_length")
        ),
        sa.CheckConstraint(
            "length(trim(label)) > 0", name=op.f("ck_acad_course_session_label_not_blank")
        ),
        sa.CheckConstraint(
            "length(room_name) <= 30", name=op.f("ck_acad_course_session_room_name_length")
        ),
        sa.CheckConstraint(
            "length(trim(room_name)) > 0",
            name=op.f("ck_acad_course_session_room_name_not_blank"),
        ),
        sa.CheckConstraint(
            "cancel_reason IS NULL OR length(cancel_reason) <= 200",
            name=op.f("ck_acad_course_session_cancel_reason_length"),
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["acad_course.id"],
            name=op.f("fk_acad_course_session_course_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_acad_course_session")),
        sa.UniqueConstraint(
            "course_id", "session_no", name=op.f("uq_acad_course_session_course_session_no")
        ),
        sa.UniqueConstraint("event_id", name=op.f("uq_acad_course_session_event_id")),
    )
    op.create_index(
        "ix_acad_course_session_org_start",
        "acad_course_session",
        ["org_id", "start_at"],
    )
    op.create_index(
        "ix_acad_course_session_course_start",
        "acad_course_session",
        ["course_id", "start_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_acad_course_session_course_start", table_name="acad_course_session")
    op.drop_index("ix_acad_course_session_org_start", table_name="acad_course_session")
    op.drop_table("acad_course_session")
    # acad_course is an external dependency owned by #1839; never drop it here.
