from dataclasses import dataclass, field
from datetime import time

from app.logic.routing.models import Stop, Connection, WalkingLink


@dataclass
class TransitGraph:
    """In-memory represenation of the transit network"""
    stops: dict[str, Stop] = field(default_factory=dict)            # atco_code -> Stop
    connections: list[Connection] = field(default_factory=list)     # sorted by departure time
    walking_links: dict[str, list[WalkingLink]] = field(default_factory=dict)  # from_stop -> links
    disrupted_routes: set[int] = field(default_factory=set)  # route_ids currently disrupted

    def connections_from(self, stop_code: str, after: time) -> list[Connection]:
        """Returns connection departing a stop after a given time, excluding disrupted routes."""
        return [c for c in self.connections 
                if c.from_stop == stop_code 
                and c.departure >= after 
                and c.route_id not in self.disrupted_routes]
        
class GraphBuilder:
    """Loads transit data from the database into a TransitGraph.
    
    Injected with a database session so it can be tested with fakes."""

    def __init__(self, db_session):
        self.db_session = db_session

    async def build(self) -> TransitGraph:
        graph = TransitGraph()
        # 1. Load stops from `stops` table -> graph.stops
        # 2. Load timetable rows, group into Connections -> graph.connections
        #    Sort connection by departure time (critical for san algorithms)
        # 3. Load walking_connectionse -> graph.walking_links
        # 4. Load active disruptions -> graph.disrupted_routes
        return graph
