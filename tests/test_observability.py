import json

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependencies import get_resume_catalog_service
from app.core.config.settings import settings
from app.core.observability import metrics
from app.core.observability.request_context import HEADER
from app.main import app
from app.workers.resume_queue import QueueStats

ADMIN_KEY = "a" * 32
USER_KEY = "u" * 32
RESUME_ID = "665f1c2b8e4a4b0012345678"


class StubCatalog:
    def get_resume(self, resume_id):
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Resume not found")

    def list_resumes(self, status_filter, limit, offset):
        return {"items": [], "total": 0, "limit": limit, "offset": offset}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    app.dependency_overrides[get_resume_catalog_service] = lambda: StubCatalog()

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


def scraped(client, headers=None):
    return client.get("/metrics", headers=headers or {})


# --------------------------------------------------------------- request ids


def test_every_response_carries_a_request_id(client):
    response = client.get("/")

    assert len(response.headers[HEADER]) >= 8


def test_a_safe_request_id_from_the_caller_is_kept(client):
    response = client.get("/", headers={HEADER: "trace-1234.abcd"})

    assert response.headers[HEADER] == "trace-1234.abcd"


@pytest.mark.parametrize("supplied", ["short", "has space in it", "line\\nbreak-123456", "x" * 100, "a;b=c,drop-table"])
def test_an_unsafe_request_id_is_replaced(client, supplied):
    response = client.get("/", headers={HEADER: supplied})

    assert response.headers[HEADER] != supplied


def test_log_lines_carry_the_request_id(client):
    lines = []
    sink = logger.add(lambda message: lines.append(message.record["extra"].get("request_id")), level="INFO")

    try:
        client.get("/api/v1/resumes/", headers={HEADER: "trace-abc12345"})
        logger.info("outside of a request")
    finally:
        logger.remove(sink)

    assert lines[-1] == "-"


def test_the_json_log_format_has_request_id_and_resume_id_fields():
    lines = []
    sink = logger.add(lines.append, serialize=True, level="INFO")

    try:
        with logger.contextualize(request_id="trace-abc12345", resume_id="r-1"):
            logger.info("hello")
    finally:
        logger.remove(sink)

    record = json.loads(lines[-1])["record"]

    assert record["extra"] == {"request_id": "trace-abc12345", "resume_id": "r-1"}


# ------------------------------------------------------------------- metrics


def sample(text, name, **labels):
    wanted = ",".join(f'{key}="{value}"' for key, value in sorted(labels.items()))

    for line in text.splitlines():
        if line.startswith(name + "{") and all(part in line for part in wanted.split(",")):
            return float(line.rsplit(" ", 1)[1])

    return None


def test_requests_are_counted_by_route_template_not_by_url(client):
    client.get(f"/api/v1/resumes/{RESUME_ID}")
    client.get("/api/v1/resumes/665f1c2b8e4a4b0087654321")

    text = scraped(client).text

    assert 'route="/api/v1/resumes/{resume_id}"' in text
    assert RESUME_ID not in text and "665f1c2b8e4a4b0087654321" not in text
    assert sample(text, "http_requests_total", route="/api/v1/resumes/{resume_id}", status="404") >= 2


def test_the_latency_histogram_is_exposed(client):
    client.get("/")

    assert "http_request_duration_seconds_bucket" in scraped(client).text


def test_unknown_paths_share_one_label(client):
    client.get("/no/such/path/1")
    client.get("/no/such/path/2")

    text = scraped(client).text

    assert 'route="unmatched"' in text
    assert "/no/such/path" not in text


def test_the_metrics_endpoint_does_not_count_itself(client):
    scraped(client)

    assert 'route="/metrics"' not in scraped(client).text


def test_metrics_need_an_admin_key_when_authentication_is_on(monkeypatch, client):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEYS", f"admin:{ADMIN_KEY},user:{USER_KEY}")

    assert scraped(client).status_code == 401
    assert scraped(client, {"X-API-Key": USER_KEY}).status_code == 403
    assert scraped(client, {"Authorization": f"Bearer {ADMIN_KEY}"}).status_code == 200


def test_queue_gauges_read_the_queue_at_scrape_time(client):
    state = {"stats": QueueStats(pending=7, processing=2, oldest_pending_seconds=42.0)}
    metrics.watch_queue(lambda: state["stats"])

    text = scraped(client).text

    assert "resume_queue_pending 7.0" in text
    assert "resume_queue_processing 2.0" in text
    assert "resume_queue_oldest_pending_seconds 42.0" in text

    state["stats"] = None  # database unreachable

    assert "resume_queue_pending NaN" in scraped(client).text


# --------------------------------------------------------------------- ready


def test_not_ready_while_the_database_is_down(client, monkeypatch):
    from app.main import mongo_db

    monkeypatch.setattr(mongo_db, "ping", lambda: False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["database"] == "disconnected"


def test_not_ready_until_the_models_are_loaded(client, monkeypatch):
    from app.main import mongo_db

    monkeypatch.setattr(mongo_db, "ping", lambda: True)
    monkeypatch.setattr(app.state, "resume_service", None, raising=False)

    body = client.get("/ready").json()

    assert body["status"] == "not_ready" and body["models"] == "loading"


def test_ready_when_everything_is_up_and_the_worker_runs(client, monkeypatch):
    from types import SimpleNamespace

    from app.main import mongo_db

    monkeypatch.setattr(mongo_db, "ping", lambda: True)
    monkeypatch.setattr(app.state, "resume_service", object(), raising=False)
    monkeypatch.setattr(app.state, "worker", SimpleNamespace(alive=True), raising=False)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["worker"] == "running"


def test_not_ready_when_the_worker_has_died(client, monkeypatch):
    from types import SimpleNamespace

    from app.main import mongo_db

    monkeypatch.setattr(mongo_db, "ping", lambda: True)
    monkeypatch.setattr(app.state, "resume_service", object(), raising=False)
    monkeypatch.setattr(app.state, "worker", SimpleNamespace(alive=False), raising=False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["worker"] == "stopped"
