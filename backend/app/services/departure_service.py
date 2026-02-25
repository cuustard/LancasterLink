"""
Departure board service – retrieves upcoming departures for a given stop.

Combines timetable data with live delay information.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_departures(
    stop_id: str,
    db: Session,
    when: Optional[datetime] = None,
    limit: int = 20,
):
    """Return upcoming departures for a stop.

    Args:
        stop_id: NaPTAN ATCO code.
        db: Database session.
        when: Point in time (defaults to now).
        limit: Maximum number of departures to return.

    Returns:
        DepartureBoardResponse schema (assembled by the route handler).
    """
    # TODO: query timetable + live_vehicles for the stop
    logger.info("Departure request for stop %s", stop_id)
    raise NotImplementedError("Departure service not yet implemented.")
