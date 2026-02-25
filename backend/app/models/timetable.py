"""SQLAlchemy ORM model for timetable entries."""

from sqlalchemy import Column, Date, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship

from app.management.data_access import Base


class TimetableEntry(Base):
    """A single scheduled stop-time within a route.

    Maps to the ``timetable`` table defined in 02-schema.sql.
    """

    __tablename__ = "timetable"

    timetable_id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=False)
    stop_atco_code = Column(
        String(20), ForeignKey("stops.atco_code"), nullable=False
    )
    stop_sequence = Column(Integer, nullable=False)
    arrival_time = Column(Time, nullable=True)
    departure_time = Column(Time, nullable=True)
    days_of_week = Column(String(20), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    # Relationships
    route = relationship("Route", back_populates="timetable_entries")
    stop = relationship("Stop", back_populates="timetable_entries")

    def __repr__(self) -> str:
        return (
            f"<TimetableEntry route={self.route_id} "
            f"stop={self.stop_atco_code} seq={self.stop_sequence}>"
        )
