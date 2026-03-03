from dataclasses import dataclass, field
from datetime import time, date
from enum import Enum

class TransportMode(Enum):
    BUS = "bus"
    TRAIN = "train"
    TRAM = "tram"
    WALK = "walk"

@dataclass(frozen=True)
class Stop:
    atco_code: str
    name: str
    locatlity_code: str
    stop_type: TransportMode
    latitude: float
    longitude: float
    hub_score: float = 0.0

@dataclass(frozen=True)
class Connection:
    """A single scheduled movement: depart stop A, arrive stop B on a trip."""
    trip_id: str    # groups connections belonging to one route
    route_id: str   
    from_stop: str  # atco code
    to_stop: str    # atco code
    departure: time
    arrival: time
    mode: TransportMode
    days_of_week: str

@dataclass(frozen=True)
class WalkingLink:
    from_stop: str  
    to_stop: str    
    walk_time_mins: float

@dataclass
class JourneyLeg:
    mode: TransportMode
    from_stop: str
    to_stop: str
    departure: time
    arrival: time
    route_id: int | None = None
    trip_id: str | None = None

@dataclass
class JourneyResult:
    legs: list[JourneyLeg] = field(default_factory=list)
    total_duration_mins: float = 0.0
    num_transfers: int = 0
    is_live_data: bool = False  # AIC-01: visual clarity flag
