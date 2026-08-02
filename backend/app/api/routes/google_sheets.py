from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings
from app.services.google_sheets_service import (
    GoogleSheetsNotConfigured,
    sync_qualifying_properties,
)

router = APIRouter()


@router.post("/google-sheets/sync")
async def sync_google_sheets(settings: AppSettings) -> dict:
    try:
        return await sync_qualifying_properties(settings)
    except GoogleSheetsNotConfigured as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
