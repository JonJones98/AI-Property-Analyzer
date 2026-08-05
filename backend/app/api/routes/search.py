from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AppSettings, DbSession, Providers
from app.models.listing import Listing
from app.providers.base import SearchCriteria
from app.providers.rentcast import RentCastApiError, RentCastQuotaExceeded
from app.schemas.listing import ListingOut
from app.services.listing_service import run_provider_search

router = APIRouter()


@router.post("/search", response_model=list[ListingOut])
async def search_listings(
    criteria: SearchCriteria,
    db: DbSession,
    providers: Providers,
    settings: AppSettings,
) -> list[ListingOut]:
    """Run a live search against every active listing provider, persist and
    score the results, and return the matching listings.
    """
    try:
        listings = await run_provider_search(db, providers, criteria, settings)
    except RentCastQuotaExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except RentCastApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    stmt = (
        select(Listing)
        .where(Listing.id.in_([listing.id for listing in listings]))
        .options(selectinload(Listing.scores))
    )
    result = await db.execute(stmt)
    hydrated_listings = result.scalars().unique().all()

    return [ListingOut.model_validate(listing) for listing in hydrated_listings]
