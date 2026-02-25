"""
Stop model – represents a NaPTAN stop-point (bus stop, tram stop, rail station).

Corresponds to the `stops` table in the database schema (02-schema.sql) and
aligns with Section 5.1 of the Design Doc where stops serve as **graph nodes**
in the time-dependent directed graph.

Fields mirror the DB columns so instances can be hydrated directly from query
results via the data-access layer.
"""

from dataclasses import dataclass, field


@dataclass
class Stop:
    """A single NaPTAN stop / station – the fundamental *node* of the routing graph."""

    atco_code: str                      # Primary key – NaPTAN AtcoCode
    name: str                           # Human-readable stop name
    stop_type: str                      # 'bus' | 'rail' | 'tram'
    latitude: float
    longitude: float
    locality_code: str | None = None    # FK → localities (NPTG grouping, DR-01)
    hub_score: float = 0.0              # RL-02 hub-priority metric (higher = busier hub)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def coords(self) -> tuple[float, float]:
        """Return (lat, lon) tuple for distance calculations."""
        return (self.latitude, self.longitude)

    def __hash__(self) -> int:
        return hash(self.atco_code)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stop):
            return NotImplemented
        return self.atco_code == other.atco_code

    def __repr__(self) -> str:
        return f"Stop({self.atco_code!r}, {self.name!r}, {self.stop_type!r})"
