"""Pure-logic tests for the RentCast provider: field mapping, unit
conversion, and cache-key determinism. No network/Redis dependency — full
provider behavior (caching, quota enforcement, live API calls) needs the
docker-compose stack, same as the DB-backed tests noted in
test_api_health.py.
"""

from app.providers.base import SearchCriteria
from app.providers.rentcast import (
    RentCastProvider,
    _acres_to_sqft,
    _cache_key,
    _to_raw_listing,
)

SAMPLE_LISTING = {
    "id": "rc-12345",
    "formattedAddress": "123 Rural Rd, Salisbury, NC 28144",
    "addressLine1": "123 Rural Rd",
    "city": "Salisbury",
    "state": "NC",
    "zipCode": "28144",
    "county": "Rowan",
    "latitude": 35.6714,
    "longitude": -80.4741,
    "propertyType": "Land",
    "lotSize": 522720,  # 12 acres
    "hoa": {"fee": 0},
    "status": "Active",
    "price": 95000,
    "listedDate": "2026-06-01T00:00:00.000Z",
    "lastSeenDate": "2026-08-01T00:00:00.000Z",
}


def test_acres_to_sqft_round_trip():
    assert _acres_to_sqft(12) == 522_720
    assert round(522_720 / 43_560, 2) == 12.0


def test_to_raw_listing_maps_core_fields():
    raw = _to_raw_listing(SAMPLE_LISTING)
    assert raw is not None
    assert raw.provider == "rentcast"
    assert raw.provider_listing_id == "rc-12345"
    assert raw.county == "Rowan"
    assert raw.price == 95000
    assert raw.acres == 12.0
    assert raw.status == "active"
    assert raw.hoa is False


def test_to_raw_listing_maps_inactive_status():
    listing = {**SAMPLE_LISTING, "status": "Inactive"}
    raw = _to_raw_listing(listing)
    assert raw is not None
    assert raw.status == "off_market"


def test_to_raw_listing_detects_hoa_fee():
    listing = {**SAMPLE_LISTING, "hoa": {"fee": 250}}
    raw = _to_raw_listing(listing)
    assert raw is not None
    assert raw.hoa is True


def test_to_raw_listing_returns_none_without_price_or_lot_size():
    assert _to_raw_listing({**SAMPLE_LISTING, "price": None}) is None
    assert _to_raw_listing({**SAMPLE_LISTING, "lotSize": None}) is None


def test_search_params_use_rentcast_range_syntax():
    provider = RentCastProvider()
    criteria = SearchCriteria(min_price=80_000, max_price=125_000, min_acres=10, max_acres=20)
    params = provider._search_params(criteria)  # noqa: SLF001
    assert params["price"] == "80000-125000"
    assert params["lotSize"] == f"{_acres_to_sqft(10)}-{_acres_to_sqft(20)}"
    assert params["propertyType"] == "Land"
    assert params["status"] == "Active"


def test_cache_key_is_deterministic_and_param_sensitive():
    key_a = _cache_key("/listings/sale", {"state": "NC", "price": "80000-125000"})
    key_b = _cache_key("/listings/sale", {"price": "80000-125000", "state": "NC"})
    key_c = _cache_key("/listings/sale", {"state": "NC", "price": "90000-125000"})

    assert key_a == key_b  # param order shouldn't matter
    assert key_a != key_c  # different params -> different key
