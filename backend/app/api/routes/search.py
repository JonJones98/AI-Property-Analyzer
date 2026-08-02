from fastapi import APIRouter

from app.api.deps import AppSettings, DbSession, Providers
from app.providers.base import SearchCriteria
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
    listings = await run_provider_search(db, providers, criteria, settings)
    return [ListingOut.model_validate(listing) for listing in listings]
