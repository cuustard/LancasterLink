"""
Router – the core journey-search algorithm for LancasterLink.

Implements a **modified Dijkstra** search over the time-dependent directed
graph built by graph_builder.py.  This is the algorithmic heart of the system
and directly addresses:

    FR-JP-01  Multi-modal routing (bus + rail + tram + walking)
    FR-JP-02  Fallback to timetable (graph is built from timetable by default)
    FR-JP-03  Disruption awareness (disrupted edges excluded in graph queries)
    FR-JP-05  Interchange buffering (fragile connections filtered by cost_function)
    RL-01     Fragile connection avoidance
    RL-02     Hub prioritisation (via reliability heuristic in cost)
    RL-04     Multi-modal stitching (walking edges connect modes)

Algorithm overview
------------------
Standard Dijkstra is adapted for a *time-dependent* graph:

1.  The search state is (stop, arrival_time, cumulative_cost).
2.  We start at the origin stop at the user's requested departure time.
3.  At each node expansion we query the graph for:
        a. Transit edges departing at or after our current time.
        b. Walking edges (always available – just add walk_time to clock).
4.  For each candidate edge we compute the total cost via cost_function.py.
5.  We reject *fragile connections* (RL-01 / FR-JP-05) where the transfer
    buffer is too short.
6.  The search terminates when we pop the destination stop from the priority
    queue, or when the queue is exhausted (no route found).
7.  We reconstruct the journey by following predecessor pointers.

The result is a JourneyPlan containing an ordered list of JourneyLeg objects.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from datetime import time, timedelta, datetime
from typing import Sequence

from app.logic.routing.graph_builder import TransportGraph, TransitEdge, WalkingEdge
from app.logic.routing.cost_function import (
    transit_edge_cost,
    walking_edge_cost,
    is_fragile_connection,
    _minutes_between,
)
from app.models.stop import Stop


# ── Result data structures ───────────────────────────────────────────────────

@dataclass
class JourneyLeg:
    """One leg of a multi-modal journey (a single vehicle ride or a walk)."""
    from_stop_atco: str
    from_stop_name: str
    to_stop_atco: str
    to_stop_name: str
    departure_time: time
    arrival_time: time
    mode: str                       # 'bus' | 'rail' | 'tram' | 'walk'
    route_id: int | None = None     # None for walking legs
    route_name: str | None = None   # e.g. 'Stagecoach 2A'
    operator: str | None = None

    @property
    def duration_mins(self) -> float:
        dep = timedelta(hours=self.departure_time.hour, minutes=self.departure_time.minute)
        arr = timedelta(hours=self.arrival_time.hour, minutes=self.arrival_time.minute)
        diff = (arr - dep).total_seconds() / 60.0
        return diff if diff >= 0 else diff + 24 * 60


@dataclass
class JourneyPlan:
    """A complete journey from origin to destination, potentially multi-modal."""
    legs: list[JourneyLeg]
    total_cost: float               # Cumulative cost (equivalent minutes)
    total_duration_mins: float      # Wall-clock minutes from first departure to final arrival
    num_transfers: int              # Number of vehicle changes

    @property
    def departure_time(self) -> time | None:
        return self.legs[0].departure_time if self.legs else None

    @property
    def arrival_time(self) -> time | None:
        return self.legs[-1].arrival_time if self.legs else None


# ── Internal search state ────────────────────────────────────────────────────

@dataclass(order=True)
class _SearchNode:
    """Priority-queue entry for Dijkstra search.

    Ordered by cumulative cost so that heapq always pops the lowest-cost node.
    """
    cost: float
    atco_code: str = field(compare=False)
    arrival_time: time = field(compare=False)
    # Predecessor information for path reconstruction
    prev_atco: str | None = field(default=None, compare=False)
    edge: TransitEdge | WalkingEdge | None = field(default=None, compare=False)


# ── The router ───────────────────────────────────────────────────────────────

# Maximum number of nodes to expand before giving up.
# Prevents runaway searches on very large graphs.  Tuned for the regional
# network (Lancaster / Preston / Blackpool) which has ~O(1000) stops.
MAX_EXPANSIONS: int = 50_000

# Maximum results to return
MAX_RESULTS: int = 5


def find_journeys(
    graph: TransportGraph,
    origin_atco: str,
    destination_atco: str,
    departure_time: time,
    max_results: int = MAX_RESULTS,
) -> list[JourneyPlan]:
    """Find the best journey(s) from *origin* to *destination* departing at
    *departure_time*.

    This is the top-level routing function called by the journey service.

    The algorithm runs a modified Dijkstra search to find the single optimal
    (lowest-cost) path first.  To offer alternatives, it re-runs the search
    while excluding the first edge of each previously found journey, yielding
    diverse route options (a simplified k-shortest-paths approach).

    Parameters
    ----------
    graph : TransportGraph
        Pre-built transport graph (from graph_builder.build_graph).
    origin_atco : str
        NaPTAN atco_code of the departure stop.
    destination_atco : str
        NaPTAN atco_code of the arrival stop.
    departure_time : time
        Desired departure time.
    max_results : int
        Maximum number of alternative journeys to return.

    Returns
    -------
    list[JourneyPlan]
        Ordered by total_cost (best first).  Empty if no route exists.
    """
    results: list[JourneyPlan] = []
    excluded_first_edges: set[tuple[str, str, int | None]] = set()

    for _ in range(max_results):
        plan = _dijkstra_search(
            graph, origin_atco, destination_atco, departure_time,
            excluded_first_edges=excluded_first_edges,
        )
        if plan is None:
            break
        results.append(plan)
        # Exclude the first edge of this journey to diversify next search
        first_leg = plan.legs[0]
        excluded_first_edges.add(
            (first_leg.from_stop_atco, first_leg.to_stop_atco, first_leg.route_id)
        )

    return results


def _dijkstra_search(
    graph: TransportGraph,
    origin_atco: str,
    destination_atco: str,
    departure_time: time,
    excluded_first_edges: set[tuple[str, str, int | None]] | None = None,
) -> JourneyPlan | None:
    """Run a single modified-Dijkstra search and return the optimal journey.

    Returns None if the destination is unreachable.
    """
    if excluded_first_edges is None:
        excluded_first_edges = set()

    # Priority queue and visited set
    pq: list[_SearchNode] = []
    best_cost: dict[str, float] = {}        # atco_code → lowest cost seen
    predecessors: dict[str, _SearchNode] = {}  # atco_code → SearchNode that reached it

    start_node = _SearchNode(
        cost=0.0,
        atco_code=origin_atco,
        arrival_time=departure_time,
    )
    heapq.heappush(pq, start_node)
    best_cost[origin_atco] = 0.0
    # Store the origin node in predecessors so reconstruction can find
    # the departure time for the first walking leg.
    predecessors[origin_atco] = start_node

    expansions = 0

    while pq and expansions < MAX_EXPANSIONS:
        current = heapq.heappop(pq)
        expansions += 1

        # Arrived at destination – reconstruct and return
        if current.atco_code == destination_atco:
            return _reconstruct(current, predecessors, graph)

        # Skip if we've already found a better path to this stop
        if current.cost > best_cost.get(current.atco_code, math.inf):
            continue

        current_stop = graph.get_stop(current.atco_code)
        if current_stop is None:
            continue

        # ── Expand transit edges ─────────────────────────────────────────
        for edge in graph.get_outgoing_transit_edges(current.atco_code, current.arrival_time):
            # If this is the first edge from origin, check exclusion list
            if current.atco_code == origin_atco:
                edge_key = (edge.from_stop, edge.to_stop, edge.route_id)
                if edge_key in excluded_first_edges:
                    continue

            # Compute edge cost
            cost = transit_edge_cost(
                edge, current.arrival_time, graph,
                # In full implementation, hub_score_max and delay ratios
                # would come from a pre-computed data structure.
                hub_score_max=1.0,
                stop_delay_ratio=0.0,
                route_delay_ratio=0.0,
            )
            if cost is None:
                continue

            # Fragile connection check (RL-01 / FR-JP-05)
            # Only relevant when transferring, i.e. the previous leg was a
            # *different* route or a walk.
            if current.edge is not None:
                is_transfer = True
                if isinstance(current.edge, TransitEdge) and current.edge.route_id == edge.route_id:
                    # Staying on the same service – not a transfer
                    is_transfer = False
                if is_transfer:
                    wait = _minutes_between(current.arrival_time, edge.departure_time)
                    if is_fragile_connection(wait, current_stop):
                        continue  # Skip this fragile connection

            new_cost = current.cost + cost
            if new_cost < best_cost.get(edge.to_stop, math.inf):
                best_cost[edge.to_stop] = new_cost
                node = _SearchNode(
                    cost=new_cost,
                    atco_code=edge.to_stop,
                    arrival_time=edge.arrival_time,
                    prev_atco=current.atco_code,
                    edge=edge,
                )
                heapq.heappush(pq, node)
                predecessors[edge.to_stop] = node

        # ── Expand walking edges ─────────────────────────────────────────
        for wedge in graph.get_walking_edges(current.atco_code):
            # If this is the first edge from origin, check exclusion list
            if current.atco_code == origin_atco:
                edge_key = (wedge.from_stop, wedge.to_stop, None)
                if edge_key in excluded_first_edges:
                    continue

            walk_cost = walking_edge_cost(wedge)
            # Compute arrival time after the walk
            walk_arrival = _add_minutes(current.arrival_time, wedge.walk_time_mins)

            new_cost = current.cost + walk_cost
            if new_cost < best_cost.get(wedge.to_stop, math.inf):
                best_cost[wedge.to_stop] = new_cost
                node = _SearchNode(
                    cost=new_cost,
                    atco_code=wedge.to_stop,
                    arrival_time=walk_arrival,
                    prev_atco=current.atco_code,
                    edge=wedge,
                )
                heapq.heappush(pq, node)
                predecessors[wedge.to_stop] = node

    # Destination was not reached
    return None


# ── Path reconstruction ──────────────────────────────────────────────────────

def _reconstruct(
    dest_node: _SearchNode,
    predecessors: dict[str, _SearchNode],
    graph: TransportGraph,
) -> JourneyPlan:
    """Walk backwards through predecessor pointers to build the JourneyPlan."""
    # Collect (edge, arrival_time_at_from_stop) pairs from destination back
    # to origin.  The arrival_time_at_from_stop lets us correctly timestamp
    # walking legs.
    path_reversed: list[tuple[TransitEdge | WalkingEdge, time]] = []
    node: _SearchNode | None = dest_node

    while node is not None and node.edge is not None:
        # The predecessor node's arrival_time tells us when we reached the
        # from_stop of this edge.
        prev_node = predecessors.get(node.prev_atco) if node.prev_atco else None  # type: ignore[arg-type]
        # For the from_stop arrival time, look up the from_stop's search node.
        # This is stored in predecessors (including the origin node).
        from_node = predecessors.get(node.edge.from_stop)
        from_arrival = from_node.arrival_time if from_node else node.arrival_time
        path_reversed.append((node.edge, from_arrival))
        node = prev_node

    path_reversed.reverse()

    # Convert edges to JourneyLeg objects, merging consecutive edges on the
    # same route into a single leg (so a bus riding through 5 stops becomes
    # one leg, not 5).
    legs: list[JourneyLeg] = []
    for edge, from_arrival_time in path_reversed:
        if isinstance(edge, TransitEdge):
            # Try to merge with the previous leg if same route
            if (
                legs
                and legs[-1].route_id == edge.route_id
                and legs[-1].to_stop_atco == edge.from_stop
            ):
                # Extend existing leg
                to_stop = graph.get_stop(edge.to_stop)
                legs[-1].to_stop_atco = edge.to_stop
                legs[-1].to_stop_name = to_stop.name if to_stop else edge.to_stop
                legs[-1].arrival_time = edge.arrival_time
            else:
                # New leg
                from_stop = graph.get_stop(edge.from_stop)
                to_stop = graph.get_stop(edge.to_stop)
                route = graph.get_route(edge.route_id)
                legs.append(JourneyLeg(
                    from_stop_atco=edge.from_stop,
                    from_stop_name=from_stop.name if from_stop else edge.from_stop,
                    to_stop_atco=edge.to_stop,
                    to_stop_name=to_stop.name if to_stop else edge.to_stop,
                    departure_time=edge.departure_time,
                    arrival_time=edge.arrival_time,
                    mode=edge.transport_mode,
                    route_id=edge.route_id,
                    route_name=route.route_name if route else None,
                    operator=route.operator if route else None,
                ))
        elif isinstance(edge, WalkingEdge):
            from_stop = graph.get_stop(edge.from_stop)
            to_stop = graph.get_stop(edge.to_stop)
            # Use the tracked arrival time at the from_stop as walk departure.
            walk_dep = from_arrival_time
            walk_arr = _add_minutes(walk_dep, edge.walk_time_mins)
            legs.append(JourneyLeg(
                from_stop_atco=edge.from_stop,
                from_stop_name=from_stop.name if from_stop else edge.from_stop,
                to_stop_atco=edge.to_stop,
                to_stop_name=to_stop.name if to_stop else edge.to_stop,
                departure_time=walk_dep,
                arrival_time=walk_arr,
                mode="walk",
            ))

    # Compute summary metrics
    total_duration = 0.0
    if legs:
        total_duration = _minutes_between(legs[0].departure_time, legs[-1].arrival_time)

    num_transfers = max(0, sum(1 for leg in legs if leg.mode != "walk") - 1)

    return JourneyPlan(
        legs=legs,
        total_cost=dest_node.cost,
        total_duration_mins=total_duration,
        num_transfers=num_transfers,
    )


# ── Private helpers ──────────────────────────────────────────────────────────

def _add_minutes(t: time, mins: float) -> time:
    """Add *mins* minutes to a time object, wrapping at midnight."""
    total_seconds = (t.hour * 3600 + t.minute * 60 + t.second) + (mins * 60)
    total_seconds %= 86400  # wrap around midnight
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    return time(h, m, s)
