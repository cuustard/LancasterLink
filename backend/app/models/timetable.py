"""
Timetable model – a single scheduled stop-time within a route.

Corresponds to the `timetable` table in 02-schema.sql.  A complete service
journey is an ordered list of TimetableEntry objects (sorted by stop_sequence)
sharing the same route_id.

In the routing graph (Design Doc §5.1), consecutive timetable entries on the
same route form the **transit edges** of the time-dependent directed graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time, date


@dataclass
class TimetableEntry:
    """One row of the timetable: a specific stop-time on a route."""

    timetable_id: int
    route_id: int                       # FK → routes
    stop_atco_code: str                 # FK → stops
    stop_sequence: int                  # Order within the route (1, 2, 3 …)
    arrival_time: time | None           # None for the first stop
    departure_time: time | None         # None for the last stop
    trip_id: str | None = None          # Groups stop-times into a single vehicle journey
    days_of_week: str | None = None     # e.g. 'MoTuWeThFr'
    valid_from: date | None = None
    valid_to: date | None = None

    def operates_on(self, query_date: date) -> bool:
        """Check whether this entry is valid for a given date.

        This is a simplified check.  A production implementation would parse
        `days_of_week` properly and compare against the calendar.
        """
        if self.valid_from and query_date < self.valid_from:
            return False
        if self.valid_to and query_date > self.valid_to:
            return False
        # Prototype: assume operates every day unless filtered out by validity range
        return True

    def __repr__(self) -> str:
        return (
            f"TimetableEntry(route={self.route_id}, stop={self.stop_atco_code!r}, "
            f"seq={self.stop_sequence}, arr={self.arrival_time}, dep={self.departure_time})"
        )
