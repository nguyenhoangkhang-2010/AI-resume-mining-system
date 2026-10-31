from types import SimpleNamespace

import mongomock
import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.core.config.settings import settings


class FakeStack:
    def __init__(self):
        self.resume_service = SimpleNamespace(process_resume=lambda resume_id, retry_possible=False: None)

    def state(self):
        return {"resume_service": self.resume_service}


@pytest.fixture
def stubbed(monkeypatch):
    """The real startup and shutdown code with the heavy parts replaced."""

    database = mongomock.MongoClient().db

    monkeypatch.setattr(main, "validate_security_settings", lambda s: None)
    monkeypatch.setattr(main, "login_huggingface", lambda: None)
    monkeypatch.setattr(main, "build_processing_stack", lambda: FakeStack())
    monkeypatch.setattr(main.mongo_db, "connect", lambda: None)
    monkeypatch.setattr(main.mongo_db, "close", lambda: None)
    monkeypatch.setattr(main.mongo_db, "ping", lambda: True)
    monkeypatch.setattr(main.mongo_db, "get_db", lambda: database)
    monkeypatch.setattr(main.FaissManager, "shutdown", lambda: None)
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "WARMUP_ENABLED", False)
    monkeypatch.setattr(settings, "WORKER_POLL_SECONDS", 0.05)
    monkeypatch.setattr(settings, "WORKER_SHUTDOWN_SECONDS", 2)

    for name in ("queue", "worker"):
        main.app.state._state.pop(name, None)

    return database


def test_the_embedded_worker_starts_with_the_api_and_stops_with_it(stubbed, monkeypatch):
    monkeypatch.setattr(settings, "PROCESSING_MODE", "queue")
    monkeypatch.setattr(settings, "WORKER_EMBEDDED", True)

    with TestClient(main.app) as client:
        worker = main.app.state.worker

        assert worker is not None and worker.alive
        assert client.get("/ready").json()["worker"] == "running"

    assert not worker.alive


def test_a_waiting_resume_is_handed_to_the_worker_after_startup(stubbed, monkeypatch):
    from datetime import datetime
    import time

    handled = []
    monkeypatch.setattr(settings, "PROCESSING_MODE", "queue")
    monkeypatch.setattr(settings, "WORKER_EMBEDDED", True)
    monkeypatch.setattr(
        FakeStack,
        "__init__",
        lambda self: setattr(
            self,
            "resume_service",
            SimpleNamespace(process_resume=lambda resume_id, retry_possible=False: handled.append(resume_id)),
        ),
    )
    stubbed["resumes"].insert_one({"upload_status": "pending", "created_at": datetime(2026, 1, 1)})

    with TestClient(main.app):
        deadline = time.monotonic() + 5

        while not handled and time.monotonic() < deadline:
            time.sleep(0.05)

    assert len(handled) == 1


def test_without_the_embedded_worker_uploads_only_wait_in_the_queue(stubbed, monkeypatch):
    monkeypatch.setattr(settings, "PROCESSING_MODE", "queue")
    monkeypatch.setattr(settings, "WORKER_EMBEDDED", False)

    with TestClient(main.app) as client:
        assert main.app.state.worker is None
        assert client.get("/ready").json()["worker"] == "n/a"


def test_inline_mode_starts_no_worker_and_no_queue(stubbed, monkeypatch):
    monkeypatch.setattr(settings, "PROCESSING_MODE", "inline")

    with TestClient(main.app):
        assert main.app.state.worker is None
        assert not hasattr(main.app.state, "queue")
