"""SQLAlchemy ORM model for NaPTAN stops."""

from geoalchemy2 import Geometry
from sqlalchemy import Column, Double, String
from sqlalchemy.orm import relationship

from app.management.data_access import Base


class Stop(Base):
    """Represents a bus stop, tram stop, or rail station (NaPTAN).

    Maps to the ``stops`` table defined in 02-schema.sql.
    """

    __tablename__ = "stops"

    atco_code = Column(String(20), primary_key=True)
    name = Column(String(255), nullable=False)
    locality_code = Column(String(20), nullable=True)
    stop_type = Column(String(20), nullable=False)
    latitude = Column(Double, nullable=False)
    longitude = Column(Double, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=True)
    hub_score = Column(Double, default=0)

    # Relationships
    timetable_entries = relationship(
        "TimetableEntry", back_populates="stop", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Stop {self.atco_code} {self.name!r}>"
