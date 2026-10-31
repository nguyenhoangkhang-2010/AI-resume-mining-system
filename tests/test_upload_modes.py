from types import SimpleNamespace

import fitz
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_resume_service
from app.api.routes.v1 import resume_routes
from app.core.config.settings import settings
from app.main import app


def pdf_bytes():
    with fitz.open() as document:
        document.new_page().insert_text((72, 72), "Backend engineer")

        return document.tobytes()


@pytest.fixture
def service(monkeypatch, tmp_path):
    events = []

    class Service:
        def create_resume(self, file_path, filename):
            events.append("created")

            return SimpleNamespace(
                id="665f1c2b8e4a4b0012345678",
                filename=filename,
                upload_status="pending",
                created_at="2026-01-01T00:00:00",
            )

        def process_resume(self, resume_id):
            events.append("processed")

    monkeypatch.setattr(resume_routes, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    app.dependency_overrides[get_resume_service] = lambda: Service()

    yield events

    app.dependency_overrides.clear()


def upload():
    return TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.pdf", pdf_bytes(), "application/pdf")},
    )


def test_in_queue_mode_the_upload_only_creates_the_pending_resume(service, monkeypatch):
    monkeypatch.setattr(settings, "PROCESSING_MODE", "queue")

    response = upload()

    assert response.status_code == 202
    assert response.json()["upload_status"] == "pending"
    assert service == ["created"]


def test_in_inline_mode_the_upload_also_runs_the_processing(service, monkeypatch):
    monkeypatch.setattr(settings, "PROCESSING_MODE", "inline")

    upload()

    assert service == ["created", "processed"]


def test_the_default_is_the_durable_queue_inside_the_api():
    assert settings.PROCESSING_MODE == "queue"
    assert settings.WORKER_EMBEDDED is True
    assert settings.WORKER_MAX_ATTEMPTS >= 2
