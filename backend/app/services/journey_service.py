"""
Journey Service – orchestrates the routing pipeline.

This is the service-layer entry point called by the API route handler
(api/routes/journey.py).  It coordinates:

    1. Fetching data from the data-access layer (stops, routes, timetable,
       walking connections, disruptions).
    2. Building the transport graph (graph_builder.build_graph).
    3. Running the routing algorithm (router.find_journeys).
    4. Formatting the result for the API response.

Design Doc §3.2 component 3a:
    "Calculates the best route possible based on distinct characteristics."

In a full implementation the graph could be cached and reused across requests,
only rebuilding when timetable data changes.  For the prototype the graph is
built per-request, which is acceptable for the evaluation load (5–10 users,
NFR-PL-03).
"""

from __future__ import annotations

from datetime import time, date
from typing import Any

from app.logic.routing.graph_builder import build_graph, TransportGraph
from app.logic.routing.router import find_journeys, JourneyPlan
from app.management.data_access import DataAccess


def plan_journey(
    origin_atco: str,
    destination_atco: str,
    departure_time: time,
    departure_date: date | None = None,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Plan a journey and return serialisable result dicts.

    Parameters
    ----------
    origin_atco : str
        NaPTAN AtcoCode of the starting stop / station.
    destination_atco : str
        NaPTAN AtcoCode of the destination stop / station.
    departure_time : time
        Desired departure time.
    departure_date : date | None
        Date of travel (defaults to today).  Used to filter timetable validity
        and to support FR-JP-04 (future planning up to 3 months ahead).
    max_results : int
        Number of alternative journeys to return.

    Returns
    -------
    list[dict]
        Each dict represents a JourneyPlan, ready for JSON serialisation by
        the API layer.
    """
    dao = DataAccess()

    # ── 1. Fetch all required data from the management/data-access layer ─────
    stops = dao.get_all_stops()
    routes = dao.get_all_routes()
    timetable = dao.get_timetable_entries(departure_date)
    walking = dao.get_walking_connections()
    disrupted_ids = dao.get_disrupted_route_ids()

    # ── 2. Build the transport graph ─────────────────────────────────────────
    # Design Doc §5.1: "The transport network will be treated as a
    # Time-Dependent Directed Graph"
    graph = build_graph(
        stops=stops,
        routes=routes,
        timetable_entries=timetable,
        walking_connections=walking,
        disrupted_route_ids=disrupted_ids,
    )

    # ── 3. Run the routing algorithm ─────────────────────────────────────────
    plans = find_journeys(
        graph=graph,
        origin_atco=origin_atco,
        destination_atco=destination_atco,
        departure_time=departure_time,
        max_results=max_results,
    )

    # ── 4. Serialise results ─────────────────────────────────────────────────
    return [_serialise_plan(plan) for plan in plans]


def _serialise_plan(plan: JourneyPlan) -> dict[str, Any]:
    """Convert a JourneyPlan into a JSON-friendly dictionary.

    This structure aligns with the /api/journey response schema that the
    frontend (JourneyResults.jsx) expects.
    """
    return {
        "departure_time": plan.departure_time.isoformat() if plan.departure_time else None,
        "arrival_time": plan.arrival_time.isoformat() if plan.arrival_time else None,
        "total_duration_mins": round(plan.total_duration_mins, 1),
        "total_cost": round(plan.total_cost, 2),
        "num_transfers": plan.num_transfers,
        "legs": [
            {
                "from": {
                    "atco_code": leg.from_stop_atco,
                    "name": leg.from_stop_name,
                },
                "to": {
                    "atco_code": leg.to_stop_atco,
                    "name": leg.to_stop_name,
                },
                "departure_time": leg.departure_time.isoformat(),
                "arrival_time": leg.arrival_time.isoformat(),
                "duration_mins": round(leg.duration_mins, 1),
                "mode": leg.mode,
                "route_name": leg.route_name,
                "operator": leg.operator,
            }
            for leg in plan.legs
        ],
    }
