"""Closed vocabularies and length limits for acad_course_session."""
from __future__ import annotations

SESSION_STATUSES = (
    "scheduled",
    "signup_open",
    "signup_closed",
    "in_progress",
    "finished",
    "cancelled",
)
LABEL_MAX_CHARS = 20
ROOM_NAME_MAX_CHARS = 30
CANCEL_REASON_MAX_CHARS = 200
CAPACITY_MIN = 1
CAPACITY_MAX = 500
WAITLIST_MIN = 0
WAITLIST_MAX = 100
CANCEL_DEADLINE_MIN_HOURS = 0
SESSION_NO_MIN = 1
STATUS_DEFAULT = "scheduled"
WAITLIST_DEFAULT = 0
CANCEL_DEADLINE_DEFAULT = 24
