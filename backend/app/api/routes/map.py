"""
Map state endpoints (Design Doc §6.3 – /api/map).

FR-LM-03: Combined map state (stops + live vehicles).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas import MapStateResponse
from app.management.data_access import get_db

router = APIRouter()


@router.get("/state", response_model=MapStateResponse)
def get_map_state(
    db: Session = Depends(get_db),
    north: float = Query(54.1),
    south: float = Query(53.7),
    east: float = Query(-2.6),
    west: float = Query(-3.0),
):
    """Return stops and live vehicles within the viewport bounds.

    Combines data needed for the initial map render and periodic
    refreshes (FR-LM-03).
    """
    # TODO: wire up map_service.get_state(bounds, db)
    return MapStateResponse(stops=[], vehicles=[])
