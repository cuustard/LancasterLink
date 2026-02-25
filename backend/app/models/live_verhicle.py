"""SQLAlchemy ORM model for live vehicle positions."""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Double, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship

from app.management.data_access import Base


class LiveVehicle(Base):
    """Real-time position of a bus, train, or tram.

    Maps to the ``live_vehicles`` table defined in 02-schema.sql.
    """

    __tablename__ = "live_vehicles"

    vehicle_id = Column(String(50), primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=True)
    latitude = Column(Double, nullable=False)
    longitude = Column(Double, nullable=False)
    bearing = Column(Double, nullable=True)
    speed = Column(Double, nullable=True)
    transport_mode = Column(String(20), nullable=False)
    last_updated = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    geom = Column(Geometry("POINT", srid=4326), nullable=True)

    # Relationships
    route = relationship("Route", back_populates="live_vehicles")

    def __repr__(self) -> str:
        return f"<LiveVehicle {self.vehicle_id} ({self.transport_mode})>"
