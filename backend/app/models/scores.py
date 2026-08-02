import uuid

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scores(Base):
    __tablename__ = "scores"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    price_score: Mapped[float | None] = mapped_column(Float)
    location_score: Mapped[float | None] = mapped_column(Float)
    build_score: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float, index=True)

    listing: Mapped["Listing"] = relationship(back_populates="scores")


from app.models.listing import Listing  # noqa: E402
