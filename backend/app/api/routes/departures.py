"""
Departure board endpoints (Design Doc §6.3 – /api/departures).

FR-DB-01: Show upcoming departures for a stop.
FR-DB-02: Show real-time expected arrival/departure times.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import DepartureBoardResponse
from app.management.data_access import get_db

router = APIRouter()


@router.get("/{stop_id}", response_model=DepartureBoardResponse)
def get_departures(stop_id: str, db: Session = Depends(get_db)):
    """Return upcoming departures for the given stop.

    Args:
        stop_id: NaPTAN ATCO code of the stop.
    """
    # TODO: wire up departure_service.get_departures(stop_id, db)
    raise NotImplementedError(
        "Departure board not yet implemented on this branch."
    )
