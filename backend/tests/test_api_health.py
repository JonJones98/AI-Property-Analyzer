"""Smoke test for the FastAPI app wiring.

Full route tests (listings/search/dashboard) require a running Postgres +
PostGIS instance (see docker-compose.yml) and are intentionally not run
against sqlite/mocks, since geoalchemy2 columns and Postgres-specific types
don't have a lightweight substitute. Run `docker compose up -d db` then
`pytest` from within the backend container for full coverage.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
