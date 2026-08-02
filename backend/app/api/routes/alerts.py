from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings
from app.services.alerts_service import send_test_alert

router = APIRouter()


@router.post("/alerts/test")
async def trigger_test_alert(channel: str, settings: AppSettings) -> dict:
    try:
        return await send_test_alert(settings, channel)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
