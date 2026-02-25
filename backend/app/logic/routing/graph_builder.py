"""
Graph Builder – constructs the time-dependent directed graph used by the router.

Design Doc §5.1 – "The transport network will be treated as a Time-Dependent
Directed Graph":
    • Nodes  → NaPTAN stop-points (Stop model)
    • Edges  → travel legs derived from timetable entries, plus walking legs
               between nearby stops of different modes (RL-04 multi-modal stitching)
    • Weights → travel time (edge traversal cost is resolved at query-time by
               the cost function, because departure availability depends on
               the current clock in the search)

This module is responsible for:
    1. Indexing all stops as graph nodes.
    2. Building transit edges from timetable entries (consecutive stops on same route).
    3. Adding walking / interchange edges from the walking_connections table.
    4. Exposing a query interface so the router can ask:
       "Given I am at stop X at time T, what edges (next-departures or walks)
        can I take from here?"
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import time, date, datetime, timedelta
from typing import Sequence

from app.models.stop import Stop
from app.models.route import Route
from app.models.timetable import TimetableEntry


# ── Edge definitions ─────────────────────────────────────────────────────────

@dataclass
class TransitEdge:
    """A timetabled travel leg between two consecutive stops on a route.

    Created from a pair of consecutive TimetableEntry objects on the same route.
    The edge encodes *when* a service departs the origin and *when* it arrives
    at the destination – making the graph time-dependent.
    """
    from_stop: str              # atco_code of origin stop
    to_stop: str                # atco_code of destination stop
    route_id: int               # FK → routes (identifies the service)
    departure_time: time        # Scheduled departure from from_stop
    arrival_time: time          # Scheduled arrival at to_stop
    transport_mode: str         # 'bus' | 'rail' | 'tram'

    @property
    def travel_minutes(self) -> float:
        """Compute scheduled travel time in minutes."""
        dep = timedelta(hours=self.departure_time.hour, minutes=self.departure_time.minute)
        arr = timedelta(hours=self.arrival_time.hour, minutes=self.arrival_time.minute)
        diff = (arr - dep).total_seconds() / 60.0
        # Handle overnight wraparound (e.g. depart 23:50 → arrive 00:10)
        if diff < 0:
            diff += 24 * 60
        return diff


@dataclass
class WalkingEdge:
    """A walking connection between two nearby stops (RL-04 multi-modal stitching).

    Always available regardless of time-of-day.  Derived from the
    `walking_connections` table in the DB schema.
    """
    from_stop: str              # atco_code
    to_stop: str                # atco_code
    walk_time_mins: float       # Walking duration in minutes
    distance_metres: float = 0.0


# ── The graph itself ─────────────────────────────────────────────────────────

class TransportGraph:
    """Time-dependent directed graph for the LancasterLink transport network.

    The graph is built once from timetable data and walking connections, then
    queried repeatedly by the router during each journey search.

    Internal storage
    ----------------
    _stops : dict[str, Stop]
        All known stops indexed by atco_code.
    _transit_edges : dict[str, list[TransitEdge]]
        Transit edges indexed by *from_stop* atco_code, sorted by departure_time
        within each list for efficient next-departure lookup.
    _walking_edges : dict[str, list[WalkingEdge]]
        Walking edges indexed by *from_stop* atco_code.
    _routes : dict[int, Route]
        Lookup table for route metadata.
    _disrupted_route_ids : set[int]
        Route IDs currently flagged as cancelled / severely delayed.
        Edges on these routes are skipped during search (FR-JP-03).
    """

    def __init__(self) -> None:
        self._stops: dict[str, Stop] = {}
        self._transit_edges: dict[str, list[TransitEdge]] = {}
        self._walking_edges: dict[str, list[WalkingEdge]] = {}
        self._routes: dict[int, Route] = {}
        self._disrupted_route_ids: set[int] = set()

    # ── Construction helpers ─────────────────────────────────────────────

    def add_stop(self, stop: Stop) -> None:
        """Register a stop as a node in the graph."""
        self._stops[stop.atco_code] = stop

    def add_route(self, route: Route) -> None:
        """Register a route for metadata lookups during result formatting."""
        self._routes[route.route_id] = route

    def add_transit_edge(self, edge: TransitEdge) -> None:
        """Add a single timetabled transit edge to the graph."""
        self._transit_edges.setdefault(edge.from_stop, []).append(edge)

    def add_walking_edge(self, edge: WalkingEdge) -> None:
        """Add a walking connection edge to the graph."""
        self._walking_edges.setdefault(edge.from_stop, []).append(edge)

    def mark_disrupted(self, route_id: int) -> None:
        """Flag a route as disrupted – its edges will be excluded from search.

        Implements FR-JP-03 (Disruption Awareness): "Route calculations must
        penalise or avoid services flagged as Cancelled or Significantly Delayed."
        """
        self._disrupted_route_ids.add(route_id)

    def clear_disruption(self, route_id: int) -> None:
        """Remove disruption flag when a service is restored."""
        self._disrupted_route_ids.discard(route_id)

    def finalise(self) -> None:
        """Sort transit edge lists by departure time for efficient lookup.

        Must be called after all edges have been added and before routing queries.
        """
        for edges in self._transit_edges.values():
            edges.sort(key=lambda e: (e.departure_time.hour, e.departure_time.minute))

    # ── Query interface (used by the router) ─────────────────────────────

    def get_stop(self, atco_code: str) -> Stop | None:
        return self._stops.get(atco_code)

    def get_route(self, route_id: int) -> Route | None:
        return self._routes.get(route_id)

    def get_all_stops(self) -> dict[str, Stop]:
        return self._stops

    def get_outgoing_transit_edges(
        self, atco_code: str, earliest_departure: time
    ) -> list[TransitEdge]:
        """Return transit edges departing from *atco_code* at or after *earliest_departure*.

        Edges belonging to disrupted routes are automatically excluded (FR-JP-03).
        """
        all_edges = self._transit_edges.get(atco_code, [])
        results: list[TransitEdge] = []
        for edge in all_edges:
            # Skip disrupted services
            if edge.route_id in self._disrupted_route_ids:
                continue
            # Only include departures at or after the requested time
            if _time_ge(edge.departure_time, earliest_departure):
                results.append(edge)
        return results

    def get_walking_edges(self, atco_code: str) -> list[WalkingEdge]:
        """Return all walking connections from *atco_code*."""
        return self._walking_edges.get(atco_code, [])


# ── Graph builder function ───────────────────────────────────────────────────

def build_graph(
    stops: Sequence[Stop],
    routes: Sequence[Route],
    timetable_entries: Sequence[TimetableEntry],
    walking_connections: Sequence[tuple[str, str, float, float]],
    disrupted_route_ids: Sequence[int] | None = None,
) -> TransportGraph:
    """Construct a TransportGraph from raw data collections.

    This is the main entry-point called by the journey service.  In a full
    implementation the data would come from the data-access layer (management/
    data_access.py → database).  For the prototype, any iterable of model
    objects works.

    Parameters
    ----------
    stops : sequence of Stop
    routes : sequence of Route
    timetable_entries : sequence of TimetableEntry
        Must be sorted (or at least grouped) by (route_id, stop_sequence).
    walking_connections : sequence of (from_atco, to_atco, walk_mins, distance_m)
    disrupted_route_ids : optional list of route IDs to exclude (FR-JP-03)

    Returns
    -------
    TransportGraph  ready for querying by the router.
    """
    graph = TransportGraph()

    # 1. Register all stops as graph nodes
    for stop in stops:
        graph.add_stop(stop)

    # 2. Register routes
    for route in routes:
        graph.add_route(route)

    # 3. Build transit edges from consecutive timetable entries on the same trip.
    #    Each "trip" is one vehicle journey along a route (e.g. the 08:00 run of
    #    bus route 40).  Two consecutive rows (stop_sequence n, n+1) on the same
    #    trip form one edge:  departure_time @ stop n  →  arrival_time @ stop n+1
    entries_by_trip: dict[tuple[int, str | None], list[TimetableEntry]] = {}
    for entry in timetable_entries:
        key = (entry.route_id, entry.trip_id)
        entries_by_trip.setdefault(key, []).append(entry)

    for (route_id, _trip_id), entries in entries_by_trip.items():
        entries.sort(key=lambda e: e.stop_sequence)
        route = graph.get_route(route_id)
        mode = route.transport_mode if route else "bus"

        for i in range(len(entries) - 1):
            curr = entries[i]
            nxt = entries[i + 1]
            # We need a departure time at the current stop and an arrival at the next
            if curr.departure_time is None or nxt.arrival_time is None:
                continue
            graph.add_transit_edge(TransitEdge(
                from_stop=curr.stop_atco_code,
                to_stop=nxt.stop_atco_code,
                route_id=route_id,
                departure_time=curr.departure_time,
                arrival_time=nxt.arrival_time,
                transport_mode=mode,
            ))

    # 4. Add walking / interchange edges (RL-04 multi-modal stitching)
    for from_atco, to_atco, walk_mins, dist_m in walking_connections:
        graph.add_walking_edge(WalkingEdge(from_atco, to_atco, walk_mins, dist_m))
        # Walking edges are bidirectional
        graph.add_walking_edge(WalkingEdge(to_atco, from_atco, walk_mins, dist_m))

    # 5. Mark disrupted routes
    if disrupted_route_ids:
        for rid in disrupted_route_ids:
            graph.mark_disrupted(rid)

    # 6. Sort edge lists for efficient querying
    graph.finalise()

    return graph


# ── Private helpers ──────────────────────────────────────────────────────────

def _time_ge(a: time, b: time) -> bool:
    """Return True if time *a* >= time *b* (ignoring date)."""
    return (a.hour, a.minute, a.second) >= (b.hour, b.minute, b.second)
