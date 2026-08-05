"""add real parcel boundary, neighbor parcels, and data source

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-05

"""
from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "parcels",
        sa.Column(
            "boundary", geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326), nullable=True
        ),
    )
    op.add_column("parcels", sa.Column("neighbor_parcels", sa.JSON(), nullable=True))
    op.add_column(
        "parcels",
        sa.Column("data_source", sa.String(16), nullable=False, server_default="estimated"),
    )


def downgrade() -> None:
    op.drop_column("parcels", "data_source")
    op.drop_column("parcels", "neighbor_parcels")
    op.drop_column("parcels", "boundary")
