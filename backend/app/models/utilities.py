import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Utilities(Base):
    __tablename__ = "utilities"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    electric: Mapped[bool | None] = mapped_column()
    internet: Mapped[bool | None] = mapped_column()
    gas: Mapped[bool | None] = mapped_column()

    listing: Mapped["Listing"] = relationship(back_populates="utilities")


from app.models.listing import Listing  # noqa: E402
