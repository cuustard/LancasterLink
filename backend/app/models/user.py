"""SQLAlchemy ORM model for saved journeys / user bookmarks."""

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func

from app.management.data_access import Base


class SavedJourney(Base):
    """A user-saved journey (FR-JP-06 COULD requirement).

    Maps to the ``saved_journeys`` table defined in 02-schema.sql.
    Uses a hashed identifier rather than storing PII.
    """

    __tablename__ = "saved_journeys"

    journey_id = Column(Integer, primary_key=True, autoincrement=True)
    user_hash = Column(String(255), nullable=True)
    origin_atco = Column(
        String(20), ForeignKey("stops.atco_code"), nullable=True
    )
    destination_atco = Column(
        String(20), ForeignKey("stops.atco_code"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<SavedJourney {self.journey_id} "
            f"{self.origin_atco} -> {self.destination_atco}>"
        )
