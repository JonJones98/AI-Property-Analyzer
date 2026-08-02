import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Flood(Base):
    __tablename__ = "floods"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    flood_zone: Mapped[str | None] = mapped_column(String(16))

    listing: Mapped["Listing"] = relationship(back_populates="flood")


from app.models.listing import Listing  # noqa: E402
