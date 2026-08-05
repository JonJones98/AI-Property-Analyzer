"""RentCast listing provider — real for-sale land listings.

RentCast (https://developers.rentcast.io) is a licensed real estate data
API; this is the app's real `ListingProvider` implementation, replacing
`MockNCLandProvider` as the active data source once `RENTCAST_API_KEY` is
set. Verified against RentCast's live API docs:

  * GET /listings/sale        — search (state/city/zip/lat-lon+radius,
                                  propertyType, price/lotSize *ranges* as
                                  "min-max", status, limit up to 500)
  * GET /listings/sale/{id}   — single listing by RentCast's internal id

Known gaps versus our data model (RentCast doesn't expose these — enrichment
still estimates them): road frontage, electric-at-road, and a public listing
URL (RentCast has no stable public listing-page URL field).

RentCast's free tier caps at 50 requests/month. Every call in this module
goes through `app.core.cache`: a 25h response cache (so the twice-daily
scheduler makes ~1 real call/day, not 2) plus a hard monthly counter that
refuses to call the API at all once the configured limit is reached, rather
than relying on caching alone to stay under quota.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.cache import cache_get_json, cache_set_json, increment_monthly_counter
from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.base import ListingProvider, RawListing, SearchCriteria

logger = get_logger(__name__)

BASE_URL = "https://api.rentcast.io/v1"
REQUEST_TIMEOUT_SECONDS = 15.0
MAX_PAGE_SIZE = 500
SQFT_PER_ACRE = 43_560

_PROPERTY_TYPE_MAP = {"vacant_land": "Land"}
_STATUS_MAP = {"Active": "active", "Inactive": "off_market"}


def _acres_to_sqft(acres: float) -> int:
    return round(acres * SQFT_PER_ACRE)


def _to_raw_listing(item: dict[str, Any]) -> RawListing | None:
    lot_size_sqft = item.get("lotSize")
    price = item.get("price")
    if lot_size_sqft is None or price is None:
        return None

    last_seen_raw = item.get("lastSeenDate") or item.get("listedDate")
    last_seen = (
        datetime.fromisoformat(last_seen_raw.replace("Z", "+00:00"))
        if last_seen_raw
        else datetime.now(UTC)
    )

    hoa_fee = (item.get("hoa") or {}).get("fee")

    return RawListing(
        provider="rentcast",
        provider_listing_id=str(item["id"]),
        address=item.get("addressLine1") or item.get("formattedAddress"),
        county=item.get("county"),
        city=item.get("city"),
        zipcode=item.get("zipCode"),
        latitude=item["latitude"],
        longitude=item["longitude"],
        price=price,
        acres=round(lot_size_sqft / SQFT_PER_ACRE, 2),
        status=_STATUS_MAP.get(item.get("status", "Active"), "active"),
        url=None,
        has_road_frontage=None,
        hoa=bool(hoa_fee) if hoa_fee is not None else None,
        electric_at_road=None,
        last_seen=last_seen,
    )


class RentCastApiError(Exception):
    """Non-retryable RentCast API failure (bad key, quota exhausted, etc.)."""


class RentCastQuotaExceeded(RentCastApiError):
    """Raised instead of calling the API once the monthly cap is reached."""


def _cache_key(path: str, params: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    return f"rentcast:{path}:{digest}"


class RentCastProvider(ListingProvider):
    key = "rentcast"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.rentcast_api_key
        self._cache_ttl_seconds = settings.rentcast_cache_ttl_seconds
        self._monthly_limit = settings.rentcast_monthly_call_limit

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        retry=retry_if_exception_type(httpx.TransportError),
    )
    async def _fetch(self, path: str, params: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                path,
                params=params,
                headers={"X-Api-Key": self._api_key},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        if response.status_code in (401, 402, 403):
            raise RentCastApiError(
                f"RentCast API rejected the request ({response.status_code}): "
                f"{response.text[:200]}"
            )
        response.raise_for_status()
        return response.json()

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        """Cached, quota-guarded RentCast request.

        Checks the 25h response cache first (free, no quota impact). Only on
        a cache miss does it check the monthly counter and, if there's
        headroom, make a real call — incrementing the counter and caching
        the result. If the monthly limit is already reached, raises instead
        of calling, so a burst of varied queries can't blow past the quota.
        """
        if not self._api_key:
            raise RentCastApiError(
                "RENTCAST_API_KEY is not set — required to use the rentcast provider."
            )

        key = _cache_key(path, params)
        cached = await cache_get_json(key)
        if cached is not None:
            logger.info("rentcast.cache_hit", path=path)
            return cached

        count = await increment_monthly_counter("rentcast", self._monthly_limit)
        if count > self._monthly_limit:
            raise RentCastQuotaExceeded(
                f"RentCast monthly call limit ({self._monthly_limit}) reached "
                f"({count} calls this month) — refusing to call the API. "
                "Cached results (25h TTL) still work; new queries won't "
                "until next month or the limit is raised."
            )

        logger.info("rentcast.api_call", path=path, monthly_call_count=count)
        result = await self._fetch(path, params)
        await cache_set_json(key, result, self._cache_ttl_seconds)
        return result

    def _search_params(self, criteria: SearchCriteria) -> dict[str, Any]:
        return {
            "state": criteria.state or "NC",
            "propertyType": _PROPERTY_TYPE_MAP.get(criteria.property_type, "Land"),
            "status": "Active",
            "price": f"{criteria.min_price}-{criteria.max_price}",
            "lotSize": f"{_acres_to_sqft(criteria.min_acres)}-{_acres_to_sqft(criteria.max_acres)}",
            "limit": MAX_PAGE_SIZE,
        }

    async def search(self, criteria: SearchCriteria) -> list[RawListing]:
        raw_items = await self._get("/listings/sale", self._search_params(criteria))
        listings = [r for item in raw_items if (r := _to_raw_listing(item)) is not None]

        if criteria.counties:
            listings = [listing for listing in listings if listing.county in criteria.counties]
        if criteria.no_hoa:
            listings = [listing for listing in listings if not listing.hoa]

        return listings

    async def get_listing(self, provider_listing_id: str) -> RawListing | None:
        try:
            item = await self._get(f"/listings/sale/{provider_listing_id}", {})
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        return _to_raw_listing(item)

    async def get_updates(self, since: datetime) -> list[RawListing]:
        """Best-effort refresh: RentCast has no "changed since" filter, so
        this re-pulls currently active NC land listings posted within the
        lookback window (`daysOld`) rather than a true diff. Price/status
        changes on already-known listings are still picked up because
        ingestion upserts by (provider, provider_listing_id) regardless.
        """
        days_old = max(1, (datetime.now(UTC) - since).days)
        params = {
            "state": "NC",
            "propertyType": _PROPERTY_TYPE_MAP["vacant_land"],
            "status": "Active",
            "daysOld": f"1-{days_old}",
            "limit": MAX_PAGE_SIZE,
        }
        raw_items = await self._get("/listings/sale", params)
        return [r for item in raw_items if (r := _to_raw_listing(item)) is not None]
