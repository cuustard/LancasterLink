"""
Reliability scoring – estimates how reliable a journey leg or
connection is, based on historical and live data.

Requirements:
    RL-03: Connection reliability heuristic.
    RL-05: Delay-penalty scoring.
"""

import logging

logger = logging.getLogger(__name__)


def connection_reliability_score(
    transfer_time_mins: float,
    mode: str,
    hub_score: float = 0.0,
) -> float:
    """Estimate the reliability of a connection/transfer.

    A higher score (0-1) means more reliable.

    Args:
        transfer_time_mins: Minutes available for the transfer.
        mode: Transport mode of the arriving service.
        hub_score: Hub importance score of the transfer stop.

    Returns:
        Float between 0.0 (unreliable) and 1.0 (very reliable).
    """
    # Rail services have higher variance → need more buffer
    min_buffer = {"rail": 8, "bus": 4, "tram": 5}.get(mode, 5)

    if transfer_time_mins < min_buffer:
        base = max(0.0, transfer_time_mins / min_buffer)
    else:
        base = min(1.0, 0.7 + 0.3 * (transfer_time_mins / (min_buffer * 2)))

    # Hubs have better interchange facilities → small boost
    hub_boost = min(0.1, hub_score * 0.02)
    return min(1.0, base + hub_boost)


def delay_penalty(
    avg_delay_mins: float,
    mode: str,
) -> float:
    """Return a cost penalty (in minutes) to discourage unreliable legs.

    Args:
        avg_delay_mins: Average observed delay for this service/route.
        mode: Transport mode.

    Returns:
        Extra cost in minutes to add to the routing cost function.
    """
    weight = {"rail": 1.5, "bus": 1.2, "tram": 1.1}.get(mode, 1.3)
    return avg_delay_mins * weight
