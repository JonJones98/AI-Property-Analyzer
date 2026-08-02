import uuid

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Distances(Base):
    """Drive-time (minutes) from the listing to key amenities."""

    __tablename__ = "distances"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    costco: Mapped[float | None] = mapped_column(Float)
    whole_foods: Mapped[float | None] = mapped_column(Float)
    walmart: Mapped[float | None] = mapped_column(Float)
    cvs: Mapped[float | None] = mapped_column(Float)
    hospital: Mapped[float | None] = mapped_column(Float)
    lowes: Mapped[float | None] = mapped_column(Float)
    home_depot: Mapped[float | None] = mapped_column(Float)
    i85: Mapped[float | None] = mapped_column(Float)

    listing: Mapped["Listing"] = relationship(back_populates="distances")


from app.models.listing import Listing  # noqa: E402
