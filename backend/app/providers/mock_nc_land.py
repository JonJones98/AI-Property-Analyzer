import random
from datetime import UTC, datetime, timedelta

from app.providers.base import ListingProvider, RawListing, SearchCriteria

# Anchor towns roughly along the I-85 corridor through NC, with approximate
# center coordinates. Used to scatter mock listings so the map / distance
# scoring has something realistic to work with until a real provider and
# real geocoding are wired in.
_I85_CORRIDOR_TOWNS: list[tuple[str, str, float, float]] = [
    ("Gaston", "Gastonia", 35.2621, -81.1873),
    ("Mecklenburg", "Charlotte", 35.2271, -80.8431),
    ("Cabarrus", "Concord", 35.4088, -80.5795),
    ("Rowan", "Salisbury", 35.6714, -80.4741),
    ("Davidson", "Lexington", 35.8240, -80.2534),
    ("Guilford", "Greensboro", 36.0726, -79.7920),
    ("Alamance", "Burlington", 36.0957, -79.4378),
    ("Orange", "Hillsborough", 36.0726, -79.0997),
    ("Durham", "Durham", 35.9940, -78.8986),
    ("Granville", "Oxford", 36.3115, -78.5911),
]

_STATUS_WEIGHTS = [("active", 0.82), ("pending", 0.1), ("sold", 0.06), ("off_market", 0.02)]


def _weighted_status(rng: random.Random) -> str:
    r = rng.random()
    cumulative = 0.0
    for status, weight in _STATUS_WEIGHTS:
        cumulative += weight
        if r <= cumulative:
            return status
    return "active"


class MockNCLandProvider(ListingProvider):
    """Deterministic fake data provider for local dev / tests.

    Generates plausible vacant-land listings scattered along the I-85
    corridor. Swap `ACTIVE_LISTING_PROVIDERS` in .env to point at a real
    provider once one is integrated — nothing else in the app needs to
    change because everything talks to the `ListingProvider` interface.
    """

    key = "mock_nc_land"

    def __init__(self, seed: int = 42, catalog_size: int = 120) -> None:
        self._seed = seed
        self._catalog_size = catalog_size

    def _generate_catalog(self) -> list[RawListing]:
        rng = random.Random(self._seed)
        listings: list[RawListing] = []
        now = datetime.now(UTC)

        for i in range(self._catalog_size):
            county, town, base_lat, base_lon = rng.choice(_I85_CORRIDOR_TOWNS)
            lat = base_lat + rng.uniform(-0.15, 0.15)
            lon = base_lon + rng.uniform(-0.15, 0.15)
            acres = round(rng.uniform(5, 35), 2)
            price_per_acre = rng.uniform(4500, 14000)
            price = round(acres * price_per_acre, -2)

            listings.append(
                RawListing(
                    provider=self.key,
                    provider_listing_id=f"mock-{i:04d}",
                    address=f"{100 + i} {town} Rd",
                    # No "County" suffix — matches real providers' format
                    # (e.g. RentCast returns "Rowan", not "Rowan County").
                    county=county,
                    city=town,
                    zipcode=f"27{i % 900:03d}",
                    latitude=round(lat, 6),
                    longitude=round(lon, 6),
                    price=price,
                    acres=acres,
                    status=_weighted_status(rng),
                    url=f"https://example-listings.local/mock/{i:04d}",
                    has_road_frontage=rng.random() > 0.15,
                    hoa=rng.random() < 0.1,
                    electric_at_road=rng.random() > 0.25,
                    last_seen=now - timedelta(hours=rng.randint(0, 72)),
                )
            )
        return listings

    async def search(self, criteria: SearchCriteria) -> list[RawListing]:
        catalog = self._generate_catalog()
        results = [
            listing
            for listing in catalog
            if listing.status == "active"
            and criteria.min_acres <= listing.acres <= criteria.max_acres
            and criteria.min_price <= listing.price <= criteria.max_price
            and (not criteria.no_hoa or not listing.hoa)
            and (not criteria.road_frontage_required or listing.has_road_frontage)
            and (not criteria.counties or listing.county in criteria.counties)
        ]
        return results

    async def get_listing(self, provider_listing_id: str) -> RawListing | None:
        catalog = self._generate_catalog()
        for listing in catalog:
            if listing.provider_listing_id == provider_listing_id:
                return listing
        return None

    async def get_updates(self, since: datetime) -> list[RawListing]:
        catalog = self._generate_catalog()
        return [listing for listing in catalog if listing.last_seen >= since]
