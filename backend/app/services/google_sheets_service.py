"""Google Sheets sync service.

Roadmap (see README): authenticate via a service account
(GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON_PATH), open
GOOGLE_SHEETS_SPREADSHEET_ID with gspread, and upsert rows across the
Dashboard / Listings / Top Picks / Rejected / Cost Estimates / Visited /
Offers / Closed tabs described in the spec — updating prices, removing sold
properties, highlighting new listings, and timestamping each sync.

Not implemented yet: this requires a real Google Cloud service account and
spreadsheet, which aren't available in this environment. The route wiring
below is final; only this function's body needs to change once credentials
exist.
"""

from app.core.config import Settings


class GoogleSheetsNotConfigured(Exception):
    pass


async def sync_qualifying_properties(settings: Settings) -> dict:
    if not settings.google_sheets_enabled:
        raise GoogleSheetsNotConfigured(
            "Set GOOGLE_SHEETS_ENABLED=true and provide a service account "
            "JSON + spreadsheet id to enable syncing."
        )
    raise NotImplementedError("Google Sheets sync is not yet implemented.")
