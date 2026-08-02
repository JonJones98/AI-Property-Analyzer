from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.logging import get_logger
from app.jobs.refresh import refresh_listings_job

logger = get_logger(__name__)

_scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    settings = get_settings()

    for hour in (settings.listing_refresh_cron_hour_1, settings.listing_refresh_cron_hour_2):
        _scheduler.add_job(
            refresh_listings_job,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f"refresh_listings_{hour}h",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    _scheduler.start()
    logger.info(
        "scheduler.started",
        hours=[settings.listing_refresh_cron_hour_1, settings.listing_refresh_cron_hour_2],
    )


def shutdown_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")
