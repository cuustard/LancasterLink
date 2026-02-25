"""
Journey planning service – orchestrates stop lookup, graph building,
and the routing algorithm.

This is the main entry point called by the /api/journey route.
"""

import logging
from sqlalchemy.orm import Session

from app.api.schemas import JourneyRequest

logger = logging.getLogger(__name__)


def plan_journey(request: JourneyRequest, db: Session):
    """Plan a journey and return ranked options.

    Steps (Design Doc §5):
        1. Resolve origin / destination to Stop objects.
        2. Build the transit graph from timetable data.
        3. Run the routing algorithm (k-shortest-paths).
        4. Enrich results with live data / disruptions.
        5. Return formatted JourneyResponse.
    """
    # TODO: implement when routing module is merged
    logger.info(
        "Journey request: %s -> %s", request.origin, request.destination
    )
    raise NotImplementedError("Journey service not yet implemented.")
