"""
Cost Function – computes the total cost of traversing an edge or making a
transfer in the routing graph.

Design Doc §5.2:
    Cost = Travel Time  +  Transfer Time  +  Reliability Heuristic

All values are expressed in **equivalent minutes** so that travel time,
waiting/transfer time, and reliability adjustments live on a single comparable
scale.

This module is called by the router (router.py) to evaluate each candidate
edge when expanding nodes during the modified-Dijkstra search.
"""

from __future__ import annotations

from datetime import time, timedelta

from app.logic.routing.graph_builder import TransitEdge, WalkingEdge, TransportGraph
from app.logic.routing.heuristics import reliability_heuristic
from app.models.stop import Stop


# ── Configuration constants ──────────────────────────────────────────────────

# Minimum connection / transfer time in minutes (RL-01 / FR-JP-05).
# Connections shorter than this are rejected as "fragile".
MIN_TRANSFER_MINS: float = 5.0

# Penalty multiplier applied to transfer/waiting time so the algorithm
# prefers direct services over connections with long waits.
# A factor of 1.0 means waiting is valued the same as travel;
# >1.0 means waiting feels "worse" than being on a vehicle.
WAIT_PENALTY_FACTOR: float = 1.5


def transit_edge_cost(
    edge: TransitEdge,
    current_time: time,
    graph: TransportGraph,
    hub_score_max: float = 1.0,
    stop_delay_ratio: float = 0.0,
    route_delay_ratio: float = 0.0,
) -> float | None:
    """Compute the total cost of taking a *transit* edge from the current time.

    Returns None if the connection is infeasible (e.g. wait time < 0, which
    shouldn't happen if the graph query is correct, but is a safety check).

    Cost breakdown
    --------------
    1. **Wait / transfer time** – how long we sit at the stop before the
       service departs.  Penalised by WAIT_PENALTY_FACTOR so the algorithm
       prefers shorter waits.
    2. **Travel time** – time spent on the vehicle between the two stops.
    3. **Reliability heuristic** – bonus for hub quality of the *destination*
       stop, penalty for delay-prone routes/stops (§5.2).

    Parameters
    ----------
    edge : TransitEdge
        The candidate edge.
    current_time : time
        The searcher's clock when arriving at the origin stop.
    graph : TransportGraph
        Used to look up Stop metadata for heuristic evaluation.
    hub_score_max : float
        Max hub score in the network (for normalisation).
    stop_delay_ratio, route_delay_ratio : float
        Historical delay ratios (see heuristics.py).

    Returns
    -------
    float | None
        Total cost in equivalent minutes, or None if infeasible.
    """
    wait_mins = _minutes_between(current_time, edge.departure_time)
    if wait_mins < 0:
        return None  # Departure already passed

    travel_mins = edge.travel_minutes

    # Reliability heuristic evaluated at the *destination* stop, because
    # that's where the passenger would transfer next.
    dest_stop = graph.get_stop(edge.to_stop)
    rel_heuristic = 0.0
    if dest_stop:
        rel_heuristic = reliability_heuristic(
            dest_stop,
            hub_score_max=hub_score_max,
            stop_delay_ratio=stop_delay_ratio,
            route_delay_ratio=route_delay_ratio,
        )

    total = (wait_mins * WAIT_PENALTY_FACTOR) + travel_mins + rel_heuristic
    return max(total, 0.0)  # cost should never be negative overall


def walking_edge_cost(edge: WalkingEdge) -> float:
    """Compute the cost of a walking edge.

    Walking is straightforward: the cost is simply the walk duration.
    No reliability heuristic is applied because walking doesn't depend on
    service reliability.
    """
    return edge.walk_time_mins


def is_fragile_connection(wait_mins: float, transfer_stop: Stop) -> bool:
    """Check whether a connection is *fragile* and should be avoided.

    Requirement RL-01 / FR-JP-05:
        "Do not provide routes with connection times less than [5] mins."
        "Avoid fragile connections (e.g., <5 min transfer at a small stop)."

    A connection at a well-served hub is less risky than one at a rural stop,
    so we relax the threshold slightly for hubs.
    """
    threshold = MIN_TRANSFER_MINS
    # Give a 1-minute tolerance at major hubs (hub_score > 0.7)
    if transfer_stop.hub_score > 0.7:
        threshold = max(threshold - 1.0, 2.0)
    return wait_mins < threshold


# ── Private helpers ──────────────────────────────────────────────────────────

def _minutes_between(t_from: time, t_to: time) -> float:
    """Minutes from *t_from* to *t_to*, handling midnight wraparound."""
    td_from = timedelta(hours=t_from.hour, minutes=t_from.minute, seconds=t_from.second)
    td_to = timedelta(hours=t_to.hour, minutes=t_to.minute, seconds=t_to.second)
    diff = (td_to - td_from).total_seconds() / 60.0
    if diff < 0:
        diff += 24 * 60
    return diff
