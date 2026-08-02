from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    alerts,
    cost_estimator,
    dashboard,
    google_sheets,
    listings,
    map_data,
    scores,
    search,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.jobs.scheduler import shutdown_scheduler, start_scheduler

settings = get_settings()
configure_logging(settings.app_debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.app_env)
    start_scheduler()
    yield
    shutdown_scheduler()
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="NC Homestead Land Finder API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_v1_prefix
    app.include_router(search.router, prefix=prefix, tags=["search"])
    app.include_router(listings.router, prefix=prefix, tags=["listings"])
    app.include_router(dashboard.router, prefix=prefix, tags=["dashboard"])
    app.include_router(map_data.router, prefix=prefix, tags=["map"])
    app.include_router(scores.router, prefix=prefix, tags=["scores"])
    app.include_router(cost_estimator.router, prefix=prefix, tags=["cost-estimator"])
    app.include_router(google_sheets.router, prefix=prefix, tags=["google-sheets"])
    app.include_router(alerts.router, prefix=prefix, tags=["alerts"])

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
