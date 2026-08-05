import math
from typing import Any

EARTH_RADIUS_MILES = 3958.8
ASSUMED_RURAL_ROAD_SPEED_MPH = 45.0


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def miles_to_minutes(miles: float, mph: float = ASSUMED_RURAL_ROAD_SPEED_MPH) -> float:
    return round((miles / mph) * 60, 1)


def polygon_geometry_to_coordinates(geometry: Any) -> list[list[float]] | None:
    """Convert a PostGIS/GeoAlchemy2 Polygon (WKBElement) into a plain
    [[lat, lon], ...] outer-ring list for JSON responses / map rendering."""
    if geometry is None:
        return None
    from geoalchemy2.shape import to_shape

    shape = to_shape(geometry)
    return [[lat, lon] for lon, lat in shape.exterior.coords]
