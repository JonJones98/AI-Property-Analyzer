from pydantic import BaseModel


class HomesteadScoreInput(BaseModel):
    """Everything the scoring engine needs about one listing.

    Assembled by the enrichment pipeline from Listing + its related
    Parcel/Soil/Flood/Buildability/Utilities/Distances rows.
    """

    price: float
    min_price: int
    max_price: int
    stretch_price: int

    acres: float
    min_acres: float
    max_acres: float

    distance_costco: float | None = None
    distance_whole_foods: float | None = None
    distance_walmart: float | None = None
    distance_cvs: float | None = None
    distance_home_depot: float | None = None
    distance_lowes: float | None = None
    distance_hospital: float | None = None
    distance_i85: float | None = None

    flood_zone: str | None = None

    electric: bool | None = None
    internet: bool | None = None
    gas: bool | None = None

    soil_rating: float | None = None
    perk_possible: bool | None = None

    estimated_site_cost: float | None = None

    tax_value: float | None = None


class HomesteadScoreResult(BaseModel):
    price_score: float
    location_score: float
    build_score: float
    overall_score: float
    color: str
    components: dict[str, float]
