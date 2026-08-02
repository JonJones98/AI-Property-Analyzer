from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for all runtime configuration.

    Every value has a sane default so the app boots without a .env file
    (useful for tests / CI); real deployments override via environment
    variables or a mounted .env.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "dev-secret-change-me"
    api_v1_prefix: str = "/api"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://homestead:homestead@localhost:5432/homestead"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    # --- Auth ---
    jwt_secret_key: str = "dev-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # --- Maps ---
    mapbox_access_token: str = ""
    google_maps_api_key: str = ""

    # --- Listing providers ---
    active_listing_providers: str = "mock_nc_land"
    listing_refresh_cron_hour_1: int = 6
    listing_refresh_cron_hour_2: int = 18

    # --- Government data sources ---
    usda_rural_eligibility_api_url: str = ""
    usda_ssurgo_api_url: str = "https://sdmdataaccess.sc.egov.usda.gov"
    fema_nfhl_api_url: str = "https://hazards.fema.gov/gis/nfhl/rest/services"
    census_api_key: str = ""
    ncdot_api_url: str = ""

    # --- Google Sheets ---
    google_sheets_enabled: bool = False
    google_sheets_spreadsheet_id: str = ""
    google_sheets_service_account_json_path: str = ""

    # --- Notifications ---
    notifications_enabled: bool = False
    sendgrid_api_key: str = ""
    notification_email_from: str = "alerts@nchomestead.local"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    push_notification_provider: str = ""

    # --- Default saved search ---
    default_search_state: str = "NC"
    default_search_min_acres: float = 10
    default_search_max_acres: float = 20
    default_search_min_price: int = 80_000
    default_search_max_price: int = 125_000
    default_search_stretch_price: int = 150_000
    default_search_highway_ref: str = "I-85"
    default_search_highway_max_minutes: int = 10

    @property
    def active_provider_keys(self) -> list[str]:
        return [p.strip() for p in self.active_listing_providers.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
