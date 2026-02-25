"""
Journey planning endpoints (Design Doc §6.3 – /api/journey).

FR-JP-01: Plan a multi-modal journey.
FR-JP-03: Up to 3 route options (k-shortest-paths).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import JourneyRequest, JourneyResponse
from app.management.data_access import get_db

router = APIRouter()


@router.post("", response_model=JourneyResponse)
def plan_journey(request: JourneyRequest, db: Session = Depends(get_db)):
    """Plan a journey between two locations.

    Delegates to the journey service / routing engine.
    """
    # TODO: wire up journey_service.plan(request, db)
    raise NotImplementedError(
        "Journey planning not yet implemented on this branch."
    )
