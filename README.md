# NC Homestead Land Finder

Automated discovery, scoring, and cost-estimation for buildable homestead
land in North Carolina — starting with the I-85 corridor, 10-20 acre vacant
land, $80k-$150k budget, no HOA, road frontage required.

This is a **phased MVP**: the full pipeline (provider search → enrichment →
Homestead Score → cost estimate → API → UI) runs end-to-end today using a
deterministic mock listing provider. Parcel enrichment (boundary, owner,
value, neighboring parcels) is **real data** from NC OneMap's free statewide
parcels API; soil/flood/distance enrichment are still deterministic stubs.
The whole system is demonstrable without any paid API keys. Swapping in the
remaining real data sources is a scoped, one-module-at-a-time follow-up —
see [Roadmap](#roadmap).

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Listing     │────▶│  Enrichment       │────▶│  Homestead Score │
│  Providers   │     │  (soil/flood/     │     │  + Cost Estimator│
│  (interface) │     │   distances)      │     │                  │
└─────────────┘     └──────────────────┘     └────────┬─────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │ PostgreSQL + PostGIS │
                                              └──────────┬──────────┘
                                                         │
                                    ┌────────────────────┼────────────────────┐
                                    ▼                    ▼                    ▼
                             FastAPI REST API    APScheduler (2x/day)   React frontend
                                    │
                       ┌────────────┴────────────┐
                       ▼                          ▼
              Google Sheets sync (stub)   Alerts: email/SMS/push (stub)
```

### Folder structure

```
backend/
  app/
    api/routes/       REST endpoints (search, listings, dashboard, map, scores, cost-estimator, google-sheets, alerts)
    core/             config (pydantic-settings), logging, JWT/security
    db/               SQLAlchemy async engine/session, declarative base
    models/           ORM models: Listing + Parcel/Soil/Flood/Buildability/Utilities/Distances/Scores
    providers/        ListingProvider interface, registry, MockNCLandProvider
    scoring/          Homestead Score engine (weights, thresholds, engine)
    cost_estimator/   Project cost + mortgage/tax/insurance/PMI engine
    services/         Ingestion pipeline, enrichment stubs, geo utilities
    jobs/             APScheduler twice-daily refresh job
  alembic/            DB migrations (hand-authored initial schema)
  tests/              pytest unit + smoke tests
frontend/
  src/
    api/              fetch client
    hooks/            TanStack Query hooks
    pages/            Dashboard, Listings, Listing Detail, Map
    components/       ScoreBadge, Nav
    types/            TypeScript mirrors of backend Pydantic schemas
docker-compose.yml    Postgres+PostGIS, Redis, backend, frontend for local dev
.github/workflows/    CI: backend lint+test (against real Postgres+PostGIS), frontend typecheck+build
```

## Quickstart

```bash
cp .env.example .env        # edit values as needed; safe defaults work out of the box
docker compose up
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173
- Postgres+PostGIS: localhost:5432
- Redis: localhost:6379

On first boot, the backend container runs `alembic upgrade head` before
starting uvicorn. To populate data, trigger a search:

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"state": "NC", "min_acres": 10, "max_acres": 20, "min_price": 80000, "max_price": 125000}'
```

This runs every active provider (`mock_nc_land` by default), enriches each
listing (soil/flood/distances/buildability), computes its Homestead Score,
and persists everything — then `/api/listings`, `/api/dashboard`, and
`/api/map` will return real data. The APScheduler job in `app/jobs/` repeats
this automatically twice a day (`LISTING_REFRESH_CRON_HOUR_1/2` in `.env`).

## Configuration

Everything tunable lives in `.env` (see `.env.example`) or in named-constant
modules (`app/scoring/thresholds.py`, `app/scoring/weights.py`,
`app/cost_estimator/constants.py`) — nothing is hardcoded inline. Key groups:

- **Database / Redis** — standard connection strings.
- **Listing providers** — `ACTIVE_LISTING_PROVIDERS` (comma-separated keys
  resolved via `app/providers/registry.py`).
- **Maps** — `MAPBOX_ACCESS_TOKEN` / `VITE_MAPBOX_ACCESS_TOKEN` (the map
  currently renders with free OpenStreetMap tiles; add a Mapbox token and
  swap the `TileLayer` URL in `frontend/src/pages/MapView.tsx` to switch).
- **Google Sheets / notifications** — disabled by default
  (`GOOGLE_SHEETS_ENABLED` / `NOTIFICATIONS_ENABLED`); routes return
  `501 Not Implemented` until real credentials + implementation are added.
- **Default saved search** — the spec's default criteria (NC, I-85 corridor,
  10-20 acres, $80k-$125k, $150k stretch) are the config defaults.

## The listing provider interface

```python
class ListingProvider(ABC):
    async def search(self, criteria: SearchCriteria) -> list[RawListing]: ...
    async def get_listing(self, provider_listing_id: str) -> RawListing | None: ...
    async def get_updates(self, since: datetime) -> list[RawListing]: ...
```

`MockNCLandProvider` (`app/providers/mock_nc_land.py`) is the only
implementation today — it deterministically generates ~120 plausible
listings scattered along the I-85 corridor so the rest of the app has
realistic data to work with. **To add a real provider** (an MLS/RESO feed, a
licensed land-listing API, a permitted county GIS export): implement the
three methods against the real source, register the class in
`PROVIDER_REGISTRY`, and add its key to `ACTIVE_LISTING_PROVIDERS` — nothing
else in the app changes, since routes/jobs only depend on the interface.

## Government data enrichment

`app/services/enrichment.py` fills in soil rating, flood zone, drive-time
distances, buildability, and parcel data for each listing. Parcel data is
**real**: `resolve_parcel` queries NC OneMap's statewide parcels
FeatureServer (`app/services/county_gis.py`) — free, no API key, covers all
100 NC counties — for the real parcel boundary, owner, parcel/land value,
and tax-use description at the listing's coordinates, plus up to 8 real
neighboring parcels within 250m for map context. If that lookup fails or
the point falls outside any mapped parcel (e.g. a mock listing's random
coordinate landing between real parcels), it falls back to a deterministic
placeholder so ingestion never hard-fails; the `Parcel.data_source` column
(`"nc_onemap"` vs `"estimated"`) and the map's legend/popups make it obvious
which listings have verified data.

Everything else is still a deterministic stub, documented with exactly
which real API should replace it:

| Stub function          | Real integration                                  |
|-------------------------|---------------------------------------------------|
| `estimate_distances`    | Google Maps Distance Matrix API                    |
| `estimate_soil`         | USDA SSURGO Soil Data Access API                   |
| `estimate_flood_zone`   | FEMA National Flood Hazard Layer (NFHL) REST service |
| elevation (in `resolve_parcel`'s fallback) | USGS Elevation Point Query Service |

Swapping a stub for the real thing only requires changing that one
function's body — the ingestion pipeline, scoring engine, and API are
unaware of the difference.

## Homestead Score

`app/scoring/engine.py` computes a 0-100 score from 12 weighted components
(price, acreage, shopping, healthcare, interstate, flood, utilities, soil,
buildability, appreciation, internet, tax rate). The product spec's weights
sum to 110 rather than 100 — rather than silently rescaling, `overall_score`
is computed as a true weighted average (`Σ(weight × score) / Σweight`),
which reproduces the spec's intended relative importance exactly regardless
of the sum. The 12 components roll up into the three sub-scores stored on
`Scores` (`price_score` / `location_score` / `build_score`) per
`app/scoring/weights.py`'s bucket definitions.

Color bands: **green** 90-100, **blue** 80-89, **yellow** 70-79, **red** below 70.

## Cost estimator

`app/cost_estimator/engine.py` estimates land purchase, site clearing,
grading, driveway, well, septic, electrical, survey, engineering, permits,
construction, and solar — then computes total project cost, down payment,
loan amount, amortized monthly mortgage, monthly taxes, insurance, and PMI
(PMI applied only below 20% down). All unit costs are named constants in
`app/cost_estimator/constants.py` for easy recalibration.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
ruff check .
pytest                      # scoring engine, cost estimator, mock provider, API health smoke test
```

`tests/test_scoring_engine.py`, `test_cost_estimator.py`, and
`test_mock_provider.py` are pure-logic unit tests with no DB dependency.
Full route/integration tests require Postgres+PostGIS (see
`docker-compose.yml` or the `postgres` service in
`.github/workflows/ci.yml`) since Listing rows use a PostGIS geometry
column with no lightweight substitute.

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

## Roadmap

Everything below is designed for but not yet wired up, in rough priority
order:

1. **Real listing provider(s)** — implement `ListingProvider` against a
   licensed land-listing API or permitted data source; register it and flip
   `ACTIVE_LISTING_PROVIDERS`.
2. **Real government data** — parcel boundaries/owner/value (`resolve_parcel`
   via NC OneMap) are done; replace the remaining three enrichment stubs
   (table above) with live USDA/FEMA/Google Maps calls. Parcel lookups
   currently have no caching (`CACHE_TTL_SECONDS` is defined but unused) —
   worth adding via Redis if listing volume grows, since ingestion currently
   makes 2 NC OneMap requests per listing on every search/refresh.
3. **Google Sheets sync** — `app/services/google_sheets_service.py` has the
   route wired to `501` until a service account + spreadsheet exist; then
   implement the Dashboard/Listings/Top Picks/Rejected/Cost
   Estimates/Visited/Offers/Closed tab sync described in the spec using
   `gspread` (already a dependency).
4. **Alerts** — `app/services/alerts_service.py` is stubbed the same way;
   needs a persisted alert-preferences table plus SendGrid/Twilio/push
   adapters (deps already pinned in `requirements.txt`).
5. **Auth** — Google OAuth + JWT scaffolding exists in `app/core/security.py`
   and `.env`, but no login routes/user table exist yet.
6. **Multi-state expansion** — `SearchCriteria.state` and the
   `default_search_*` settings are already parameterized per state; adding
   SC/VA/GA/TN/TX means new corridor/hub coordinate sets in
   `app/services/enrichment.py` and `app/providers/mock_nc_land.py` (or a
   real provider that already covers them).
7. **AI Property Analyzer** — an LLM-backed step that reads each enriched
   listing (score breakdown, soil/flood/buildability, cost estimate) and
   generates a short pros/risks/zoning-concerns/recommendation summary, so
   dozens of listings can be triaged in minutes. Natural integration point:
   a new `app/services/ai_analyzer.py` called after scoring in
   `listing_service.enrich_and_score_listing`, with the summary surfaced on
   the Listing Detail page and included in the Google Sheets Top Picks tab.

## Deployment

The app is Dockerized (`backend/Dockerfile`, `frontend/Dockerfile`) and
`docker-compose.yml` covers local dev. For a hosted deployment (Railway,
Render, or AWS ECS/RDS), point `DATABASE_URL` at a managed Postgres+PostGIS
instance, `REDIS_URL` at a managed Redis, set real secrets for
`APP_SECRET_KEY`/`JWT_SECRET_KEY`, and run `alembic upgrade head` as a
release step before starting `uvicorn app.main:app`.
