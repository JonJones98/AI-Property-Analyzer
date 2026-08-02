from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.providers.registry import get_active_providers
from app.services.listing_service import run_provider_updates

logger = get_logger(__name__)


async def refresh_listings_job() -> None:
    """Twice-daily refresh: pull updates from every active provider,
    re-enrich, and re-score. Runs in its own DB session since it fires
    outside of any HTTP request.
    """
    settings = get_settings()
    providers = get_active_providers(settings.active_provider_keys)
    since = datetime.now(UTC) - timedelta(hours=12)

    logger.info("refresh_job.start", providers=[p.key for p in providers], since=since.isoformat())

    async with AsyncSessionLocal() as db:
        listings = await run_provider_updates(db, providers, settings, since=since)

    logger.info("refresh_job.complete", updated_count=len(listings))
