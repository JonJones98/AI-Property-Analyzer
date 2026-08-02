import uuid

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Buildability(Base):
    __tablename__ = "buildability"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    well_required: Mapped[bool | None] = mapped_column()
    septic_required: Mapped[bool | None] = mapped_column()
    estimated_site_cost: Mapped[float | None] = mapped_column(Float)

    listing: Mapped["Listing"] = relationship(back_populates="buildability")


from app.models.listing import Listing  # noqa: E402
