"""Client for NC OneMap's statewide parcels FeatureServer.

Free, public, no authentication required — a single endpoint covering all
100 NC counties plus the Eastern Band of Cherokee Indians (avoids needing
per-county integrations). Source: NC OneMap "Parcels with Statewide
Standardized Attributes" (Integrated Cadastral Data Exchange project).

Endpoint verified live: GET {NC_ONEMAP_PARCELS_URL}/query returns GeoJSON
with fields parno/ownname/gisacres/parval/landval/siteadd/cntyname/
parusedesc and real polygon boundaries.
"""

from typing import Any, TypedDict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

REQUEST_TIMEOUT_SECONDS = 10.0
NEIGHBOR_RADIUS_METERS = 250
MAX_NEIGHBOR_PARCELS = 8
QUERY_OUT_FIELDS = "parno,ownname,gisacres,parval,landval,siteadd,cntyname,parusedesc"


class ParcelQueryError(Exception):
    """Raised when the FeatureServer returns HTTP 200 with an error body.

    ArcGIS REST services report request errors (e.g. an invalid `distance=0`
    parameter) as a 200 response containing an `{"error": ...}` payload
    rather than a 4xx/5xx status, so `response.raise_for_status()` alone
    won't catch them.
    """


class ParcelRecord(TypedDict):
    parcel_number: str | None
    owner: str | None
    acres: float | None
    parcel_value: float | None
    land_value: float | None
    site_address: str | None
    county: str | None
    use_description: str | None
    boundary: list[list[float]]  # [[lat, lon], ...] outer ring


def _feature_to_record(feature: dict[str, Any]) -> ParcelRecord | None:
    geometry = feature.get("geometry")
    if not geometry or geometry.get("type") != "Polygon":
        return None
    rings = geometry.get("coordinates") or []
    if not rings or not rings[0]:
        return None

    boundary = [[lat, lon] for lon, lat in rings[0]]
    props = feature.get("properties", {})

    return ParcelRecord(
        parcel_number=props.get("parno"),
        owner=props.get("ownname"),
        acres=props.get("gisacres"),
        parcel_value=props.get("parval"),
        land_value=props.get("landval"),
        site_address=props.get("siteadd"),
        county=props.get("cntyname"),
        use_description=props.get("parusedesc"),
        boundary=boundary,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
async def _query(
    client: httpx.AsyncClient, base_url: str, lat: float, lon: float, distance: float | None
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": QUERY_OUT_FIELDS,
        "returnGeometry": "true",
        "f": "geojson",
    }
    # ArcGIS rejects `distance=0` with a 200-status error body — omit the
    # buffer entirely for a plain point-in-polygon test instead of passing 0.
    if distance:
        params["distance"] = distance
        params["units"] = "esriSRUnit_Meter"

    response = await client.get(
        f"{base_url}/query", params=params, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise ParcelQueryError(f"NC OneMap query error: {body['error']}")
    return body.get("features", [])


async def get_subject_and_neighbor_parcels(
    lat: float, lon: float
) -> tuple[ParcelRecord | None, list[ParcelRecord]]:
    """Look up the real parcel at (lat, lon) plus nearby parcels for map context.

    Returns (subject, neighbors). Either may be empty if NC OneMap has no
    coverage at that exact location (rare, but some rural updates lag).
    Callers should fall back to estimated data on empty/failed results.
    """
    settings = get_settings()
    base_url = settings.nc_onemap_parcels_url

    async with httpx.AsyncClient() as client:
        subject_features = await _query(client, base_url, lat, lon, distance=None)
        subject = _feature_to_record(subject_features[0]) if subject_features else None

        nearby_features = await _query(
            client, base_url, lat, lon, distance=NEIGHBOR_RADIUS_METERS
        )

    subject_parno = subject["parcel_number"] if subject else None
    seen = {subject_parno} if subject_parno else set()
    neighbors: list[ParcelRecord] = []
    for feature in nearby_features:
        record = _feature_to_record(feature)
        if record is None or record["parcel_number"] in seen:
            continue
        seen.add(record["parcel_number"])
        neighbors.append(record)
        if len(neighbors) >= MAX_NEIGHBOR_PARCELS:
            break

    return subject, neighbors
