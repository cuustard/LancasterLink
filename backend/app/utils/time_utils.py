"""
Time-related utility functions used across the backend.
"""

from datetime import datetime, time, timedelta, timezone

# Lancaster sits in the UK timezone (GMT / BST).  For simplicity we
# default to UTC internally and only localise for display.
UK_TZ = timezone.utc  # Replace with zoneinfo.ZoneInfo("Europe/London") if needed


def now_utc() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def time_diff_minutes(t1: time, t2: time) -> float:
    """Return the difference in minutes between two ``time`` objects.

    Assumes both are on the same day.  If t2 < t1, assumes t2 is the
    next day (wraps past midnight).
    """
    d1 = timedelta(hours=t1.hour, minutes=t1.minute, seconds=t1.second)
    d2 = timedelta(hours=t2.hour, minutes=t2.minute, seconds=t2.second)
    diff = d2 - d1
    if diff.total_seconds() < 0:
        diff += timedelta(days=1)
    return diff.total_seconds() / 60.0


def add_minutes_to_time(t: time, minutes: float) -> time:
    """Add ``minutes`` to a ``time`` object, wrapping past midnight."""
    dt = datetime.combine(datetime.min, t) + timedelta(minutes=minutes)
    return dt.time()


def iso_format(dt: datetime) -> str:
    """Return an ISO-8601 string (used in API responses)."""
    return dt.isoformat()
