from datetime import UTC, datetime, timedelta

import pytest

from app.providers.base import SearchCriteria
from app.providers.mock_nc_land import MockNCLandProvider


@pytest.fixture
def provider() -> MockNCLandProvider:
    return MockNCLandProvider(seed=1, catalog_size=200)


async def test_search_respects_default_criteria(provider: MockNCLandProvider):
    criteria = SearchCriteria()
    results = await provider.search(criteria)

    assert results, "expected at least one matching mock listing"
    for listing in results:
        assert criteria.min_acres <= listing.acres <= criteria.max_acres
        assert criteria.min_price <= listing.price <= criteria.max_price
        assert listing.status == "active"
        assert listing.has_road_frontage is not False
        assert listing.hoa is not True


async def test_search_filters_by_county(provider: MockNCLandProvider):
    all_results = await provider.search(SearchCriteria())
    counties = {listing.county for listing in all_results}
    target_county = next(iter(counties))

    filtered = await provider.search(SearchCriteria(counties=[target_county]))
    assert filtered
    assert all(listing.county == target_county for listing in filtered)


async def test_get_listing_returns_none_for_unknown_id(provider: MockNCLandProvider):
    assert await provider.get_listing("does-not-exist") is None


async def test_get_updates_since_recent_cutoff_returns_subset(provider: MockNCLandProvider):
    since = datetime.now(UTC) - timedelta(hours=1)
    updates = await provider.get_updates(since)
    all_listings = await provider.get_updates(datetime.min.replace(tzinfo=UTC))
    assert len(updates) <= len(all_listings)
