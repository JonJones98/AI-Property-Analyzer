import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings, DbSession
from app.scoring.engine import compute_homestead_score
from app.scoring.schemas import HomesteadScoreInput, HomesteadScoreResult
from app.services.listing_service import get_listing

router = APIRouter()


@router.get("/scores/{listing_id}", response_model=HomesteadScoreResult)
async def get_score_breakdown(
    listing_id: uuid.UUID, db: DbSession, settings: AppSettings
) -> HomesteadScoreResult:
    """Return the full component-by-component Homestead Score breakdown for
    a listing, recomputed live from its currently stored enrichment data.
    """
    listing = await get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    distances = listing.distances
    soil = listing.soil
    flood = listing.flood
    buildability = listing.buildability
    utilities = listing.utilities
    parcel = listing.parcel

    score_input = HomesteadScoreInput(
        price=listing.price,
        min_price=settings.default_search_min_price,
        max_price=settings.default_search_max_price,
        stretch_price=settings.default_search_stretch_price,
        acres=listing.acres,
        min_acres=settings.default_search_min_acres,
        max_acres=settings.default_search_max_acres,
        distance_costco=distances.costco if distances else None,
        distance_whole_foods=distances.whole_foods if distances else None,
        distance_walmart=distances.walmart if distances else None,
        distance_cvs=distances.cvs if distances else None,
        distance_home_depot=distances.home_depot if distances else None,
        distance_lowes=distances.lowes if distances else None,
        distance_hospital=distances.hospital if distances else None,
        distance_i85=distances.i85 if distances else None,
        flood_zone=flood.flood_zone if flood else None,
        electric=utilities.electric if utilities else None,
        internet=utilities.internet if utilities else None,
        gas=utilities.gas if utilities else None,
        soil_rating=soil.soil_rating if soil else None,
        perk_possible=soil.perk_possible if soil else None,
        estimated_site_cost=buildability.estimated_site_cost if buildability else None,
        tax_value=parcel.tax_value if parcel else None,
    )
    return compute_homestead_score(score_input)
