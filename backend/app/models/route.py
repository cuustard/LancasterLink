"""SQLAlchemy ORM model for operator routes/services."""

from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.management.data_access import Base


class Route(Base):
    """An operator service definition (e.g. Stagecoach Route 1).

    Maps to the ``routes`` table defined in 02-schema.sql.
    """

    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, autoincrement=True)
    operator = Column(String(100), nullable=False)
    route_name = Column(String(255), nullable=False)
    transport_mode = Column(String(20), nullable=False)
    route_geom = Column(Geometry("LINESTRING", srid=4326), nullable=True)

    # Relationships
    timetable_entries = relationship(
        "TimetableEntry", back_populates="route", lazy="select"
    )
    live_vehicles = relationship(
        "LiveVehicle", back_populates="route", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Route {self.route_id} {self.route_name!r} ({self.transport_mode})>"
