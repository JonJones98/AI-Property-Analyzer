import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Parcel(Base):
    __tablename__ = "parcels"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    parcel_number: Mapped[str | None] = mapped_column(String(64), index=True)
    owner: Mapped[str | None] = mapped_column(String(255))
    tax_value: Mapped[float | None] = mapped_column(Float)
    zoning: Mapped[str | None] = mapped_column(String(64))
    road_frontage: Mapped[bool | None] = mapped_column()
    utilities: Mapped[str | None] = mapped_column(String(255))
    elevation_ft: Mapped[float | None] = mapped_column(Float)

    listing: Mapped["Listing"] = relationship(back_populates="parcel")


from app.models.listing import Listing  # noqa: E402
