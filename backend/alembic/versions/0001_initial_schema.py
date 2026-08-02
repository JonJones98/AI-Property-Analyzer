"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-02

"""
from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

listing_status = sa.Enum("active", "pending", "sold", "off_market", name="listingstatus")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "listings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("provider_listing_id", sa.String(128), nullable=False),
        sa.Column("address", sa.String(255)),
        sa.Column("county", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("zipcode", sa.String(10)),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column(
            "location", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=True
        ),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("acres", sa.Float, nullable=False),
        sa.Column("price_per_acre", sa.Float, nullable=False),
        sa.Column("status", listing_status, nullable=False, server_default="active"),
        sa.Column("url", sa.String(1024)),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_listings_provider", "listings", ["provider"])
    op.create_index("ix_listings_provider_listing_id", "listings", ["provider_listing_id"])
    op.create_index("ix_listings_county", "listings", ["county"])
    op.create_index("ix_listings_status", "listings", ["status"])

    op.create_table(
        "parcels",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("parcel_number", sa.String(64)),
        sa.Column("owner", sa.String(255)),
        sa.Column("tax_value", sa.Float),
        sa.Column("zoning", sa.String(64)),
        sa.Column("road_frontage", sa.Boolean),
        sa.Column("utilities", sa.String(255)),
    )
    op.create_index("ix_parcels_parcel_number", "parcels", ["parcel_number"])

    op.create_table(
        "soils",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("soil_type", sa.String(128)),
        sa.Column("perk_possible", sa.Boolean),
        sa.Column("soil_rating", sa.Float),
    )

    op.create_table(
        "floods",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("flood_zone", sa.String(16)),
    )

    op.create_table(
        "buildability",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("well_required", sa.Boolean),
        sa.Column("septic_required", sa.Boolean),
        sa.Column("estimated_site_cost", sa.Float),
    )

    op.create_table(
        "utilities",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("electric", sa.Boolean),
        sa.Column("internet", sa.Boolean),
        sa.Column("gas", sa.Boolean),
    )

    op.create_table(
        "distances",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("costco", sa.Float),
        sa.Column("whole_foods", sa.Float),
        sa.Column("walmart", sa.Float),
        sa.Column("cvs", sa.Float),
        sa.Column("hospital", sa.Float),
        sa.Column("lowes", sa.Float),
        sa.Column("home_depot", sa.Float),
        sa.Column("i85", sa.Float),
    )

    op.create_table(
        "scores",
        sa.Column(
            "listing_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("price_score", sa.Float),
        sa.Column("location_score", sa.Float),
        sa.Column("build_score", sa.Float),
        sa.Column("overall_score", sa.Float),
    )
    op.create_index("ix_scores_overall_score", "scores", ["overall_score"])


def downgrade() -> None:
    op.drop_table("scores")
    op.drop_table("distances")
    op.drop_table("utilities")
    op.drop_table("buildability")
    op.drop_table("floods")
    op.drop_table("soils")
    op.drop_table("parcels")
    op.drop_table("listings")
    listing_status.drop(op.get_bind(), checkfirst=True)
