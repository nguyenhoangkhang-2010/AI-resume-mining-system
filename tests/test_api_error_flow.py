import pytest
from fastapi.testclient import TestClient
from pymongo.errors import ConnectionFailure

from app.api.dependencies import get_matching_service
from app.core.exceptions import DatabaseUnavailableError
from app.database.mongodb import connection as connection_module
from app.database.mongodb.connection import mongo_db
from app.main import app
from app.services.matching_service import MatchingService


class FakeCollection:
    def find_one(self, query):
        return None


@pytest.fixture
def client():
    service = MatchingService.__new__(MatchingService)

    app.dependency_overrides[get_matching_service] = lambda: service

    yield TestClient(app, raise_server_exceptions=False), service

    app.dependency_overrides.clear()


def test_match_unknown_job_returns_404(client, monkeypatch):
    http, _ = client

    monkeypatch.setattr(
        MatchingService,
        "jobs_col",
        property(lambda self: FakeCollection()),
    )

    response = http.get("/api/v1/matches/665f1c2b8e4a4b0012345678")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert "665f1c2b8e4a4b0012345678" in response.json()["detail"]


def test_match_malformed_job_id_returns_404(client, monkeypatch):
    http, _ = client

    monkeypatch.setattr(
        MatchingService,
        "jobs_col",
        property(lambda self: FakeCollection()),
    )

    response = http.get("/api/v1/matches/not-an-object-id")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_match_with_database_down_returns_503(client, monkeypatch):
    http, _ = client

    def unavailable(self):
        raise DatabaseUnavailableError("MongoDB is not connected.")

    monkeypatch.setattr(MatchingService, "jobs_col", property(unavailable))

    response = http.get("/api/v1/matches/665f1c2b8e4a4b0012345678")

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"


def test_health_reports_connected(monkeypatch):
    monkeypatch.setattr(mongo_db, "ping", lambda: True)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_health_reports_degraded_with_503(monkeypatch):
    monkeypatch.setattr(mongo_db, "ping", lambda: False)

    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "disconnected"}


class FailingClient:
    closed = False

    def __init__(self, *args, **kwargs):
        pass

    @property
    def admin(self):
        raise ConnectionFailure("cannot reach server")

    def close(self):
        FailingClient.closed = True


def test_get_db_raises_database_unavailable_and_stays_retryable(monkeypatch):
    monkeypatch.setattr(mongo_db, "client", None)
    monkeypatch.setattr(mongo_db, "db", None)
    monkeypatch.setattr(connection_module, "MongoClient", FailingClient)

    with pytest.raises(DatabaseUnavailableError):
        mongo_db.get_db()

    # A failed connect must not leave a half-initialised client behind,
    # otherwise later calls would think MongoDB is already connected.
    assert mongo_db.client is None
    assert FailingClient.closed


def test_ping_is_false_without_client(monkeypatch):
    monkeypatch.setattr(mongo_db, "client", None)

    assert mongo_db.ping() is False


def test_mongo_uri_credentials_are_masked_in_logs():
    masked = connection_module._mask_credentials(
        "mongodb://user:secret@host:27017/"
    )

    assert "secret" not in masked
    assert "user" not in masked
