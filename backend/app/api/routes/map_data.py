from typing import Any

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.listing import ListingFilterParams
from app.scoring.engine import score_color
from app.services import listing_service

router = APIRouter()


@router.get("/map")
async def get_map_data(db: DbSession) -> dict[str, Any]:
    """GeoJSON FeatureCollection of active listings, colored by Homestead Score."""
    listings = await listing_service.list_listings(
        db, ListingFilterParams(status=None, limit=1000, offset=0)
    )

    features = []
    for listing in listings:
        overall = listing.scores.overall_score if listing.scores else None
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [listing.longitude, listing.latitude],
                },
                "properties": {
                    "id": str(listing.id),
                    "address": listing.address,
                    "county": listing.county,
                    "price": listing.price,
                    "acres": listing.acres,
                    "price_per_acre": listing.price_per_acre,
                    "status": listing.status.value,
                    "overall_score": overall,
                    "score_color": score_color(overall) if overall is not None else None,
                    "flood_zone": listing.flood.flood_zone if listing.flood else None,
                    "soil_rating": listing.soil.soil_rating if listing.soil else None,
                    "perk_possible": listing.soil.perk_possible if listing.soil else None,
                    "estimated_site_cost": (
                        listing.buildability.estimated_site_cost if listing.buildability else None
                    ),
                    "elevation_ft": listing.parcel.elevation_ft if listing.parcel else None,
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
