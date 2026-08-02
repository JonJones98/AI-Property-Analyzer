import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Soil(Base):
    __tablename__ = "soils"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    soil_type: Mapped[str | None] = mapped_column(String(128))
    perk_possible: Mapped[bool | None] = mapped_column()
    soil_rating: Mapped[float | None] = mapped_column(Float)

    listing: Mapped["Listing"] = relationship(back_populates="soil")


from app.models.listing import Listing  # noqa: E402
