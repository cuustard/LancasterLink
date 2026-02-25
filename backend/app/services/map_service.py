"""
Map service – supplies combined stop + live vehicle data for the map view.
"""

import logging
from sqlalchemy.orm import Session

from app.api.schemas import MapBounds

logger = logging.getLogger(__name__)


def get_map_state(bounds: MapBounds, db: Session):
    """Return stops and live vehicles within the given viewport bounds.

    Args:
        bounds: Bounding box from the client.
        db: Database session.

    Returns:
        MapStateResponse schema.
    """
    # TODO: spatial query for stops + live_vehicles within bounds
    logger.info("Map state request: %s", bounds)
    raise NotImplementedError("Map service not yet implemented.")
