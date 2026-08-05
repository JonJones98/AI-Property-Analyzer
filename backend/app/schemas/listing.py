import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.listing import ListingStatus


class NeighborParcelOut(BaseModel):
    parcel_number: str | None = None
    owner: str | None = None
    acres: float | None = None
    boundary: list[list[float]] | None = None


class ParcelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    parcel_number: str | None
    owner: str | None
    tax_value: float | None
    zoning: str | None
    road_frontage: bool | None
    utilities: str | None
    elevation_ft: float | None
    data_source: str
    neighbor_parcels: list[NeighborParcelOut] | None

    # Raw PostGIS geometry isn't JSON-serializable; excluded from output and
    # converted to plain [lat, lon] pairs by `boundary_coordinates` below.
    boundary: Any = Field(default=None, exclude=True)

    @computed_field
    @property
    def boundary_coordinates(self) -> list[list[float]] | None:
        from app.services.geo import polygon_geometry_to_coordinates

        return polygon_geometry_to_coordinates(self.boundary)


class SoilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    soil_type: str | None
    perk_possible: bool | None
    soil_rating: float | None


class FloodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    flood_zone: str | None


class BuildabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    well_required: bool | None
    septic_required: bool | None
    estimated_site_cost: float | None


class UtilitiesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    electric: bool | None
    internet: bool | None
    gas: bool | None


class DistancesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    costco: float | None
    whole_foods: float | None
    walmart: float | None
    cvs: float | None
    hospital: float | None
    lowes: float | None
    home_depot: float | None
    i85: float | None


class ScoresOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    price_score: float | None
    location_score: float | None
    build_score: float | None
    overall_score: float | None

    @computed_field
    @property
    def color(self) -> str | None:
        from app.scoring.engine import score_color

        return score_color(self.overall_score) if self.overall_score is not None else None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    address: str | None
    county: str | None
    city: str | None
    zipcode: str | None
    latitude: float
    longitude: float
    price: float
    acres: float
    price_per_acre: float
    status: ListingStatus
    url: str | None
    last_updated: datetime
    scores: ScoresOut | None = None


class ListingDetailOut(ListingOut):
    parcel: ParcelOut | None = None
    soil: SoilOut | None = None
    flood: FloodOut | None = None
    buildability: BuildabilityOut | None = None
    utilities: UtilitiesOut | None = None
    distances: DistancesOut | None = None


class ListingFilterParams(BaseModel):
    county: str | None = None
    status: ListingStatus | None = None
    min_price: float | None = None
    max_price: float | None = None
    min_acres: float | None = None
    max_acres: float | None = None
    min_score: float | None = None
    no_hoa: bool | None = None
    road_frontage: bool | None = None
    limit: int = 50
    offset: int = 0


class CountyBreakdown(BaseModel):
    county: str
    count: int
    avg_price: float


class DashboardOut(BaseModel):
    properties_found: int
    average_price: float
    average_price_per_acre: float
    top_homestead_score: float | None
    best_deal_listing_id: uuid.UUID | None
    new_today: int
    county_breakdown: list[CountyBreakdown]
