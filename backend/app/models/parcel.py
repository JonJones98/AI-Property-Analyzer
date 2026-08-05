import uuid

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Float, ForeignKey, String
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

    # Real parcel boundary + nearby parcels from NC OneMap (app/services/county_gis.py),
    # when available. `data_source` is "nc_onemap" for verified real data or "estimated"
    # when the lookup failed/found no coverage and enrichment fell back to the stub.
    boundary: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=True
    )
    neighbor_parcels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    data_source: Mapped[str] = mapped_column(String(16), default="estimated")

    listing: Mapped["Listing"] = relationship(back_populates="parcel")


from app.models.listing import Listing  # noqa: E402
