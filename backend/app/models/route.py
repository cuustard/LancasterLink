"""
Route model – represents an operator service definition.

Corresponds to the `routes` table in 02-schema.sql.  A route groups a sequence
of timetable entries that share the same operator, name, and transport mode
(e.g. Stagecoach service 2A, or Northern's Lancaster–Preston rail service).
"""

from dataclasses import dataclass


@dataclass
class Route:
    """An operator's named service (e.g. 'Stagecoach 2A' or 'Northern Lancaster–Preston')."""

    route_id: int                       # PK from routes table
    operator: str                       # e.g. 'Stagecoach', 'Northern', 'Blackpool Transport'
    route_name: str                     # e.g. '2A', 'Lancaster–Blackpool North'
    transport_mode: str                 # 'bus' | 'rail' | 'tram'

    def __repr__(self) -> str:
        return f"Route({self.route_id}, {self.operator!r}, {self.route_name!r}, {self.transport_mode!r})"
