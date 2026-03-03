from datetime import time, date

from app.logic.routing.graph_builder import TransitGraph
from app.logic.routing.models import JourneyResult, JourneyLeg, TransportMode

MIN_TRANSFER_TIME_MINS = 5

class Router:
    """Multi-model journey planner using a scab-based approach
    
    Design goals:
      - FR-JP-01: multi-modal (bus/rail/tram + walking links)
      - FR-JP-03: skip disrupted routes (via graph.disrupted_routes)
      - FR-JP-05: enforce minimum interchange time
      - RL-02: prefer high hub_score stops for transfers
      - NFR-PL-01: respond within 5 seconds"""

    def __init__(self, graph: TransitGraph):
        self._graph = graph

    def plan(
        self,
        origin: str,        # atco_code or locality_code
        destination: str,   # atco_code or locality_code
        depart_at: time,
        travel_date: date
    ) -> list[JourneyResult]:
        """Return ranked journey options from origin to destination.
        
        Algorithm outline (simplified RAPTOR-like):
        
        1. Resolve origin/destination to concrete stop(s).
        - If a locality_code is given, expand to all stops in that locality.
        
        2. Iinitialise earliest-arrival table:
           earliest[stop] = infinity for all stops
           earliest[origin_stops] = depart_at
           
        3. For each round k = 0, 1, 2, ... (max transferse):
           a. for each stop marked as "improved" in round k=1:
              - Scan connection departing after earliest[stop] + MIN_TRANSFER_TIME_MINS
              - If arrival at to_stop < earliest[to_stop], update it and record the leg.
           b. Expand walking link from all improved stops:
              - If walk arrival < earliest[neighbour], update it and record the leg.
           c. If destination is reached and no improvements found, stop
           
        4. Reconstruct journey legs by backtracking from destination.
        
        5. Return results sorted by: total_duration, then fewest transfers."""
           
        # TODO: implement
        raise NotImplementedError("Routing algorithm not implemented yet")
    
    def _resolve_stops(self, code: str) -> list[str]:
        """Resolve an locality code to its constituent stop or atco_codes,
        or return [code] if it's already an atco_code.
        
        Supports DR=01: linking NaPTAN sopts to NPTG localities."""

        if code in self._graph.stops:
            return [code]
        # Expand locality to all stops in that locality
        return [
            s.atco_code for s in self._graph.stops.values()
            if s.locatlity_code == code
        ]
    
    def _apply_hub_preference(self, stop_code: str, base_cost: float) -> float:
        """RL-02: Reduce effective cost for transfers at high hub-score stops."""
        stop = self._graph.stops[stop_code]
        if stop and stop.hub_score > 0:
            return base_cost * (1.0 - min(stop.hub_score, 0.5))   # up to 50% discount
        return base_cost
