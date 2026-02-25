"""
Data Access Layer – abstracts database queries for the rest of the application.

Design Doc §3.2 component 2c:
    "Handles requests from logic processing to correctly search the database."

This is a stub/prototype implementation that returns empty collections.
In the full implementation, each method will execute SQL queries against the
PostgreSQL/PostGIS database via SQLAlchemy (see 02-schema.sql for table
definitions).  The interface is defined here so that the routing algorithm
can be developed and tested independently of the database.
"""

from __future__ import annotations

from datetime import date
from typing import Sequence

from app.models.stop import Stop
from app.models.route import Route
from app.models.timetable import TimetableEntry


class DataAccess:
    """Data access object – single point of contact for all DB reads.

    TODO: Inject a SQLAlchemy session or connection pool via __init__.
    """

    def get_all_stops(self) -> list[Stop]:
        """Return all NaPTAN stops in the network.

        Production query:
            SELECT atco_code, name, stop_type, latitude, longitude,
                   locality_code, hub_score
            FROM stops;
        """
        # Stub – return empty list until DB layer is wired up
        return []

    def get_all_routes(self) -> list[Route]:
        """Return all operator routes.

        Production query:
            SELECT route_id, operator, route_name, transport_mode
            FROM routes;
        """
        return []

    def get_timetable_entries(self, query_date: date | None = None) -> list[TimetableEntry]:
        """Return timetable entries valid for *query_date*.

        Production query:
            SELECT * FROM timetable
            WHERE (valid_from IS NULL OR valid_from <= :date)
              AND (valid_to   IS NULL OR valid_to   >= :date);
        """
        return []

    def get_walking_connections(self) -> list[tuple[str, str, float, float]]:
        """Return walking connections as (from_atco, to_atco, walk_mins, distance_m).

        Production query:
            SELECT from_atco_code, to_atco_code, walk_time_mins, distance_metres
            FROM walking_connections;
        """
        return []

    def get_disrupted_route_ids(self) -> list[int]:
        """Return IDs of routes currently flagged as cancelled or severely delayed.

        Production query:
            SELECT DISTINCT route_id FROM disruptions
            WHERE disruption_type IN ('cancelled', 'delayed')
              AND severity = 'severe'
              AND start_time <= NOW()
              AND (end_time IS NULL OR end_time >= NOW());
        """
        return []
