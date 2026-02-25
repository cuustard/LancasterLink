"""
Reliability Heuristics – scoring functions that influence route cost beyond
raw travel time.

Design Doc §5.2:
    "The Routing Algorithm will not just look for the fastest time, instead
     it will look for the lowest cost."

    Cost = Travel Time + Transfer Time + **Reliability Heuristic**

The reliability heuristic is composed of two variables:
    1. Hub Prioritisation  (RL-02) – busier hubs get a *bonus* (lower cost).
    2. Delay Anticipation  – stops / routes prone to delays get a *penalty*.

Both are expressed in **equivalent minutes** so they can be added directly to
travel and transfer times in the cost function.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.models.stop import Stop


# ── Configuration constants ──────────────────────────────────────────────────
# These would ideally come from app/config.py or environment variables.
# Kept here as module-level constants for the prototype.

# Maximum bonus (negative cost) applied to the best hub.  A well-served hub
# like Preston or Lancaster rail station might save up to this many "equivalent
# minutes" compared to transferring at a small roadside stop.
HUB_MAX_BONUS_MINS: float = 5.0

# Maximum penalty applied to the most delay-prone stops / routes.
DELAY_MAX_PENALTY_MINS: float = 10.0


# ── Hub-priority score ───────────────────────────────────────────────────────

def hub_bonus(stop: Stop, hub_score_max: float = 1.0) -> float:
    """Return a *negative* cost adjustment (bonus) for well-served hubs (RL-02).

    The `hub_score` field on each Stop (mirrored from the `stops.hub_score`
    database column) represents how many services pass through the stop
    relative to the busiest hub in the network.  A value of 1.0 means it is
    the busiest; 0.0 means it has very few services.

    Hub Prioritisation rationale (Design Doc §5.2):
        "Stations and stops that facilitate more routes/services over a given
         period will have a smaller heuristic."

    A higher hub_score → bigger bonus → lower overall cost → the router
    prefers transferring at well-connected hubs.

    Parameters
    ----------
    stop : Stop
        The stop being evaluated.
    hub_score_max : float
        The maximum hub_score in the network (used for normalisation).
        Defaults to 1.0 if scores are already normalised.

    Returns
    -------
    float
        A non-positive value in equivalent minutes (0.0 to -HUB_MAX_BONUS_MINS).
    """
    if hub_score_max <= 0:
        return 0.0
    normalised = min(stop.hub_score / hub_score_max, 1.0)
    return -HUB_MAX_BONUS_MINS * normalised


# ── Delay-anticipation penalty ───────────────────────────────────────────────

def delay_penalty(
    stop_delay_ratio: float = 0.0,
    route_delay_ratio: float = 0.0,
) -> float:
    """Return a *positive* cost adjustment (penalty) for delay-prone services.

    Delay Anticipation rationale (Design Doc §5.2):
        "Stations and stops that are more prone to delays … will have a
         greater heuristic."

    The ratios are expected to be in [0, 1], where 1.0 means "always delayed."
    In the full implementation, these would be computed from historical live-
    feed data stored in the DB.  For the prototype, they are passed in as
    parameters (defaulting to 0 = no delay history available).

    Parameters
    ----------
    stop_delay_ratio : float
        Fraction of services at this stop that have been delayed recently.
    route_delay_ratio : float
        Fraction of recent runs of this route that were delayed.

    Returns
    -------
    float
        A non-negative value in equivalent minutes (0.0 to DELAY_MAX_PENALTY_MINS).
    """
    # Combine stop-level and route-level ratios (equal weighting for prototype)
    combined = (stop_delay_ratio + route_delay_ratio) / 2.0
    combined = max(0.0, min(combined, 1.0))  # clamp
    return DELAY_MAX_PENALTY_MINS * combined


# ── Aggregate reliability heuristic ──────────────────────────────────────────

def reliability_heuristic(
    stop: Stop,
    hub_score_max: float = 1.0,
    stop_delay_ratio: float = 0.0,
    route_delay_ratio: float = 0.0,
) -> float:
    """Compute the total reliability heuristic for arriving at / transferring
    through a stop.

    This is the value added to *Cost = Travel Time + Transfer Time +
    **Reliability Heuristic*** in the cost function (cost_function.py).

    Returns
    -------
    float
        Equivalent minutes – may be negative (hub bonus dominates) or positive
        (delay penalty dominates).
    """
    bonus = hub_bonus(stop, hub_score_max)
    penalty = delay_penalty(stop_delay_ratio, route_delay_ratio)
    return bonus + penalty
