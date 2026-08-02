import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.models.listing import ListingStatus
from app.schemas.listing import ListingDetailOut, ListingFilterParams, ListingOut
from app.services import listing_service

router = APIRouter()


@router.get("/listings", response_model=list[ListingOut])
async def get_listings(
    db: DbSession,
    county: str | None = None,
    status: ListingStatus | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_acres: float | None = None,
    max_acres: float | None = None,
    min_score: float | None = None,
    road_frontage: bool | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[ListingOut]:
    filters = ListingFilterParams(
        county=county,
        status=status,
        min_price=min_price,
        max_price=max_price,
        min_acres=min_acres,
        max_acres=max_acres,
        min_score=min_score,
        road_frontage=road_frontage,
        limit=limit,
        offset=offset,
    )
    listings = await listing_service.list_listings(db, filters)
    return [ListingOut.model_validate(listing) for listing in listings]


@router.get("/listing/{listing_id}", response_model=ListingDetailOut)
async def get_listing_detail(listing_id: uuid.UUID, db: DbSession) -> ListingDetailOut:
    listing = await listing_service.get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingDetailOut.model_validate(listing)
