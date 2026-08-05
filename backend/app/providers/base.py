from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel, Field

# NC counties the I-85 corridor passes through (Gastonia -> Charlotte ->
# Concord -> Salisbury -> Lexington -> Greensboro -> Burlington ->
# Hillsborough/Durham -> Oxford), matching real providers' `county` field
# format (no "County" suffix — e.g. RentCast returns "Rowan", not
# "Rowan County"). This is the product's core defining search constraint
# ("within 30 miles of I-85"), so it's the default rather than something
# every caller has to remember to pass.
I85_CORRIDOR_COUNTIES: list[str] = [
    "Gaston",
    "Mecklenburg",
    "Cabarrus",
    "Rowan",
    "Davidson",
    "Guilford",
    "Alamance",
    "Orange",
    "Durham",
    "Granville",
]


class SearchCriteria(BaseModel):
    """Search parameters a provider must be able to filter on.

    Kept provider-agnostic — no field here should assume a particular
    listing source's quirks. Providers translate this into their own
    query params internally.
    """

    state: str = "NC"
    property_type: str = "vacant_land"
    min_acres: float = 10
    max_acres: float = 20
    min_price: int = 80_000
    max_price: int = 125_000
    counties: list[str] = Field(default_factory=lambda: list(I85_CORRIDOR_COUNTIES))
    no_hoa: bool = True
    road_frontage_required: bool = True


class RawListing(BaseModel):
    """Normalized shape every provider must return, regardless of source.

    This is intentionally provider-neutral and does not include derived
    fields (scores, distances, soil, flood) — those are filled in by
    downstream enrichment services after ingestion.
    """

    provider: str
    provider_listing_id: str
    address: str | None = None
    county: str | None = None
    city: str | None = None
    zipcode: str | None = None
    latitude: float
    longitude: float
    price: float
    acres: float
    status: str = "active"
    url: str | None = None
    has_road_frontage: bool | None = None
    hoa: bool | None = None
    electric_at_road: bool | None = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    @property
    def price_per_acre(self) -> float:
        return round(self.price / self.acres, 2) if self.acres else 0.0


class ListingProvider(ABC):
    """Interface every listing data source must implement.

    Concrete providers (MLS aggregators, county GIS feeds, scraped-with-
    permission sources, etc.) are registered in
    `app.providers.registry.PROVIDER_REGISTRY` and are fully interchangeable
    from the rest of the app's point of view — nothing outside this module
    should import a concrete provider class directly.
    """

    #: unique key used in ACTIVE_LISTING_PROVIDERS / the registry
    key: str

    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> list[RawListing]:
        """Return listings matching the given criteria."""

    @abstractmethod
    async def get_listing(self, provider_listing_id: str) -> RawListing | None:
        """Fetch the current state of a single listing by its provider id."""

    @abstractmethod
    async def get_updates(self, since: datetime) -> list[RawListing]:
        """Return listings that changed (price, status, new) since `since`."""
