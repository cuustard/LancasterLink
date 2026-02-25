"""
Disruption handler – checks active disruptions and adjusts journey
plans accordingly.

Requirements:
    FR-JP-05: Flag disrupted routes and suggest alternatives.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_active_disruptions(
    db: Session,
    route_id: Optional[int] = None,
    stop_atco: Optional[str] = None,
    at_time: Optional[datetime] = None,
):
    """Fetch currently active disruptions, optionally filtered.

    Args:
        db: Database session.
        route_id: Filter by route (optional).
        stop_atco: Filter by stop (optional).
        at_time: Point in time to check (defaults to now).

    Returns:
        List of Disruption ORM objects.
    """
    # TODO: query disruptions table with time/route/stop filters
    logger.info("Checking disruptions route=%s stop=%s", route_id, stop_atco)
    return []


def is_route_disrupted(route_id: int, db: Session) -> bool:
    """Quick check whether a route has any active disruptions."""
    disruptions = get_active_disruptions(db, route_id=route_id)
    return len(disruptions) > 0
