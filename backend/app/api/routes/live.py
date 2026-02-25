"""
Live vehicle endpoints (Design Doc §6.3 – /api/live).

FR-LM-01: Display live bus positions.
FR-LM-02: Display live train positions.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas import LiveVehiclesResponse
from app.management.data_access import get_db

router = APIRouter()


@router.get("/buses", response_model=LiveVehiclesResponse)
def get_live_buses(
    db: Session = Depends(get_db),
    north: float = Query(54.1, description="Bounding box north"),
    south: float = Query(53.7, description="Bounding box south"),
    east: float = Query(-2.6, description="Bounding box east"),
    west: float = Query(-3.0, description="Bounding box west"),
):
    """Return live bus positions within the viewport."""
    # TODO: wire up live vehicle query
    return LiveVehiclesResponse(vehicles=[], count=0)


@router.get("/trains", response_model=LiveVehiclesResponse)
def get_live_trains(
    db: Session = Depends(get_db),
    north: float = Query(54.1, description="Bounding box north"),
    south: float = Query(53.7, description="Bounding box south"),
    east: float = Query(-2.6, description="Bounding box east"),
    west: float = Query(-3.0, description="Bounding box west"),
):
    """Return live train positions within the viewport."""
    # TODO: wire up live vehicle query
    return LiveVehiclesResponse(vehicles=[], count=0)
