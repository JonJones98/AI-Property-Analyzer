from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.listing import DashboardOut
from app.services.listing_service import dashboard_metrics

router = APIRouter()


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(db: DbSession) -> DashboardOut:
    metrics = await dashboard_metrics(db)
    return DashboardOut.model_validate(metrics)
