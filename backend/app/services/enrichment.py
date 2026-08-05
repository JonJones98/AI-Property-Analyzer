"""Enrichment: fill in soil / flood / distances / buildability / parcel data
for a listing.

Parcel data (`resolve_parcel`) now uses NC OneMap's real statewide parcels
FeatureServer — see `app.services.county_gis` — falling back to the
deterministic stub below only if that lookup fails or has no coverage at
the listing's coordinates (e.g. the API is unreachable, or a mock listing's
random coordinates happen to land outside any mapped parcel).

Everything else here is still a deterministic placeholder seeded by the
listing's own coordinates/id so results are stable across refreshes.
Replace each with a real integration as credentials become available:

  * distances  -> Google Maps Distance Matrix API (drive time)
  * soil       -> USDA SSURGO Soil Data Access API
  * flood_zone -> FEMA National Flood Hazard Layer (NFHL) REST service
  * elevation  -> USGS Elevation Point Query Service

Swapping a stub for the real thing only requires changing the function body
here — callers (the ingestion service) are unaware of the difference.
"""

import hashlib
import random
from typing import Any

import httpx
from tenacity import RetryError

from app.core.logging import get_logger
from app.providers.base import RawListing
from app.services import county_gis
from app.services.geo import haversine_miles, miles_to_minutes

logger = get_logger(__name__)

# Retail/hospital "hub" towns along the I-85 corridor, used as a proxy for
# nearest-store drive time until real Places/Distance-Matrix data is wired in.
_COMMON_RETAIL_HUBS: list[tuple[str, float, float]] = [
    ("Gastonia", 35.2621, -81.1873),
    ("Charlotte", 35.2271, -80.8431),
    ("Concord", 35.4088, -80.5795),
    ("Salisbury", 35.6714, -80.4741),
    ("Lexington", 35.8240, -80.2534),
    ("Greensboro", 36.0726, -79.7920),
    ("Burlington", 36.0957, -79.4378),
    ("Durham", 35.9940, -78.8986),
]

# Costco / Whole Foods are far less ubiquitous than Walmart/CVS, so only the
# larger metros count as a hub for those two.
_MAJOR_METRO_HUBS: list[tuple[str, float, float]] = [
    ("Charlotte", 35.2271, -80.8431),
    ("Greensboro", 36.0726, -79.7920),
    ("Durham", 35.9940, -78.8986),
]

_SOIL_TYPES = ["Cecil sandy loam", "Pacolet sandy loam", "Wilkes loam", "Mecklenburg loam"]
_FLOOD_ZONES = ["X", "X500", "AE", "A"]

# Elevation proxy: the NC Piedmont rises gently to the north and west toward
# the foothills/mountains, so a simple linear gradient from a reference point
# gives plausible-looking values until real DEM/USGS elevation data is wired in.
_NC_PIEDMONT_LAT_REFERENCE = 35.5
_NC_PIEDMONT_LON_REFERENCE = 80.0
_ELEVATION_BASE_FT = 250
_ELEVATION_LAT_FT_PER_DEGREE = 1600
_ELEVATION_LON_FT_PER_DEGREE = 250
_FLOOD_ZONE_WEIGHTS = [0.75, 0.15, 0.07, 0.03]


def _seeded_random(listing: RawListing) -> random.Random:
    digest = hashlib.sha256(listing.provider_listing_id.encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _nearest_hub_minutes(lat: float, lon: float, hubs: list[tuple[str, float, float]]) -> float:
    miles = min(haversine_miles(lat, lon, hub_lat, hub_lon) for _, hub_lat, hub_lon in hubs)
    return miles_to_minutes(miles)


def estimate_distances(listing: RawListing) -> dict[str, float]:
    lat, lon = listing.latitude, listing.longitude
    common = _nearest_hub_minutes(lat, lon, _COMMON_RETAIL_HUBS)
    major = _nearest_hub_minutes(lat, lon, _MAJOR_METRO_HUBS)
    i85 = _nearest_hub_minutes(lat, lon, _COMMON_RETAIL_HUBS)  # corridor towns sit on I-85
    return {
        "costco": major,
        "whole_foods": major,
        "walmart": common,
        "cvs": common,
        "home_depot": common,
        "lowes": common,
        "hospital": common,
        "i85": i85,
    }


def estimate_soil(listing: RawListing) -> dict[str, float | str | bool]:
    rng = _seeded_random(listing)
    perk_possible = rng.random() > 0.15
    return {
        "soil_type": rng.choice(_SOIL_TYPES),
        "perk_possible": perk_possible,
        "soil_rating": round(rng.uniform(40, 95) if perk_possible else rng.uniform(10, 45), 1),
    }


def estimate_flood_zone(listing: RawListing) -> str:
    rng = _seeded_random(listing)
    return rng.choices(_FLOOD_ZONES, weights=_FLOOD_ZONE_WEIGHTS, k=1)[0]


def estimate_buildability(listing: RawListing, soil_rating: float) -> dict[str, float | bool]:
    rng = _seeded_random(listing)
    base_site_cost = listing.acres * rng.uniform(800, 2500)
    if soil_rating < 40:
        base_site_cost *= 1.4  # poor soil -> more site prep
    return {
        "well_required": True,
        "septic_required": True,
        "estimated_site_cost": round(base_site_cost, 2),
    }


def estimate_utilities(listing: RawListing) -> dict[str, bool]:
    rng = _seeded_random(listing)
    electric = (
        bool(listing.electric_at_road)
        if listing.electric_at_road is not None
        else rng.random() > 0.2
    )
    return {
        "electric": electric,
        "internet": rng.random() > 0.3,
        "gas": rng.random() > 0.7,
    }


def _estimate_elevation_ft(listing: RawListing, rng: random.Random) -> float:
    lat_delta = abs(listing.latitude - _NC_PIEDMONT_LAT_REFERENCE)
    lon_delta = abs(listing.longitude + _NC_PIEDMONT_LON_REFERENCE)
    lat_component = lat_delta * _ELEVATION_LAT_FT_PER_DEGREE
    lon_component = lon_delta * _ELEVATION_LON_FT_PER_DEGREE
    return round(_ELEVATION_BASE_FT + lat_component + lon_component + rng.uniform(-80, 80), 1)


def _estimate_parcel_fallback(listing: RawListing) -> dict[str, Any]:
    """Used when NC OneMap has no coverage at these coordinates, or the
    request failed — keeps ingestion working even if the GIS service is
    down or a mock listing's random point misses real parcel data."""
    rng = _seeded_random(listing)
    return {
        "parcel_number": f"{listing.county or 'NC'}-{listing.provider_listing_id}".upper(),
        "owner": None,
        "tax_value": round(listing.price * rng.uniform(0.6, 0.9), 2),
        "zoning": "RA" if listing.county else None,
        "road_frontage": listing.has_road_frontage,
        "utilities": None,
        "elevation_ft": _estimate_elevation_ft(listing, rng),
        "boundary": None,
        "neighbor_parcels": None,
        "data_source": "estimated",
    }


async def resolve_parcel(listing: RawListing) -> dict[str, Any]:
    """Real parcel lookup via NC OneMap, with a fallback to estimated data.

    `boundary` is a shapely-ready value for the PostGIS geometry column
    (see `app.models.parcel.Parcel.boundary`); `neighbor_parcels` is a
    JSON-serializable list of nearby real parcels for map context.
    """
    fallback = _estimate_parcel_fallback(listing)

    try:
        subject, neighbors = await county_gis.get_subject_and_neighbor_parcels(
            listing.latitude, listing.longitude
        )
    except (httpx.HTTPError, RetryError, county_gis.ParcelQueryError) as exc:
        # RetryError wraps the underlying httpx exception after retries are
        # exhausted (see the @retry decorator in county_gis._query) and is
        # not an httpx.HTTPError subclass, so it needs its own branch here.
        logger.warning(
            "parcel_lookup.failed",
            provider_listing_id=listing.provider_listing_id,
            error=str(exc),
        )
        return fallback

    if subject is None:
        logger.info(
            "parcel_lookup.no_coverage", provider_listing_id=listing.provider_listing_id
        )
        return fallback

    return {
        "parcel_number": subject["parcel_number"] or fallback["parcel_number"],
        "owner": subject["owner"],
        "tax_value": subject["parcel_value"] or subject["land_value"],
        # NC OneMap's `parusedesc` is the tax parcel *use* code description
        # (e.g. "VACANT RESIDENTIAL"), not a formal zoning designation —
        # closest real attribute available until a county zoning API is added.
        "zoning": subject["use_description"] or fallback["zoning"],
        "road_frontage": listing.has_road_frontage,
        "utilities": None,
        "elevation_ft": fallback["elevation_ft"],
        "boundary": subject["boundary"],
        "neighbor_parcels": [
            {
                "parcel_number": n["parcel_number"],
                "owner": n["owner"],
                "acres": n["acres"],
                "boundary": n["boundary"],
            }
            for n in neighbors
        ],
        "data_source": "nc_onemap",
    }
