"""
Pydantic schemas for API request validation and response serialisation.

Follows the API contract in Design Doc §6.3.
"""

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field


# ── Stop schemas ─────────────────────────────────────────────────────────

class StopOut(BaseModel):
    """Public representation of a stop / station."""
    atco_code: str
    name: str
    stop_type: str
    latitude: float
    longitude: float
    hub_score: float = 0

    model_config = {"from_attributes": True}


# ── Journey planning ────────────────────────────────────────────────────

class JourneyRequest(BaseModel):
    """POST /api/journey – plan a journey."""
    origin: str = Field(..., description="Origin ATCO code or search term")
    destination: str = Field(..., description="Destination ATCO code or search term")
    depart_at: Optional[datetime] = Field(
        None, description="Desired departure time (ISO-8601). Defaults to now."
    )
    arrive_by: Optional[datetime] = Field(
        None, description="Desired arrival time (ISO-8601). Mutually exclusive with depart_at."
    )
    modes: list[str] = Field(
        default_factory=lambda: ["bus", "rail", "tram"],
        description="Transport modes to include.",
    )
    max_results: int = Field(3, ge=1, le=10, description="Number of journey options.")


class JourneyLegOut(BaseModel):
    """A single leg of a journey."""
    mode: str
    route_name: Optional[str] = None
    operator: Optional[str] = None
    origin_stop: StopOut
    destination_stop: StopOut
    departure_time: datetime
    arrival_time: datetime
    duration_mins: float
    is_walking: bool = False


class JourneyPlanOut(BaseModel):
    """A complete journey option returned to the client."""
    legs: list[JourneyLegOut]
    total_duration_mins: float
    total_changes: int
    departure_time: datetime
    arrival_time: datetime


class JourneyResponse(BaseModel):
    """Wrapper for the journey planning response."""
    journeys: list[JourneyPlanOut]
    origin: StopOut
    destination: StopOut


# ── Departure board ──────────────────────────────────────────────────────

class DepartureOut(BaseModel):
    """A single upcoming departure from a stop."""
    route_name: str
    operator: str
    destination: str
    scheduled_time: time
    expected_time: Optional[time] = None
    transport_mode: str
    status: str = "on_time"  # "on_time", "delayed", "cancelled"


class DepartureBoardResponse(BaseModel):
    """GET /api/departures/{stop_id} response."""
    stop: StopOut
    departures: list[DepartureOut]


# ── Live vehicles ────────────────────────────────────────────────────────

class LiveVehicleOut(BaseModel):
    """Live position of a single vehicle."""
    vehicle_id: str
    route_name: Optional[str] = None
    latitude: float
    longitude: float
    bearing: Optional[float] = None
    speed: Optional[float] = None
    transport_mode: str
    last_updated: datetime

    model_config = {"from_attributes": True}


class LiveVehiclesResponse(BaseModel):
    """GET /api/live/{mode} response."""
    vehicles: list[LiveVehicleOut]
    count: int


# ── Map state ────────────────────────────────────────────────────────────

class MapBounds(BaseModel):
    """Viewport bounding box."""
    north: float
    south: float
    east: float
    west: float


class MapStateResponse(BaseModel):
    """GET /api/map/state response – combined data for the live map."""
    stops: list[StopOut]
    vehicles: list[LiveVehicleOut]
