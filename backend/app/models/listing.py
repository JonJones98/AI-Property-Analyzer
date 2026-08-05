import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.buildability import Buildability
    from app.models.distances import Distances
    from app.models.flood import Flood
    from app.models.parcel import Parcel
    from app.models.scores import Scores
    from app.models.soil import Soil
    from app.models.utilities import Utilities


class ListingStatus(StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    OFF_MARKET = "off_market"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_listing_id: Mapped[str] = mapped_column(String(128), index=True)

    address: Mapped[str | None] = mapped_column(String(255))
    county: Mapped[str | None] = mapped_column(String(100), index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    zipcode: Mapped[str | None] = mapped_column(String(10))

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )

    price: Mapped[float] = mapped_column(Float)
    acres: Mapped[float] = mapped_column(Float)
    price_per_acre: Mapped[float] = mapped_column(Float)

    status: Mapped[ListingStatus] = mapped_column(
        Enum(
            ListingStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ListingStatus.ACTIVE,
        index=True,
    )
    url: Mapped[str | None] = mapped_column(String(1024))

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parcel: Mapped["Parcel | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    soil: Mapped["Soil | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    flood: Mapped["Flood | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    buildability: Mapped["Buildability | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    utilities: Mapped["Utilities | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    distances: Mapped["Distances | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    scores: Mapped["Scores | None"] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
