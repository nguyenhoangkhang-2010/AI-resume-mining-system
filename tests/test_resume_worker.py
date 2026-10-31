import threading
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

import mongomock
import pytest
from bson import ObjectId

from app.services.resume_service import ResumeService
from app.workers.resume_queue import ResumeQueue
from app.workers.resume_worker import ResumeWorker

START = datetime(2026, 1, 1, 12, 0, 0)
LONG_TEXT = "Backend engineer with several years of experience. " * 3


class FileDataError(Exception):
    """Named like the PDF library error for a damaged file: never retried."""


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def resumes():
    return mongomock.MongoClient().db["resumes"]


@pytest.fixture
def queue(resumes, clock):
    return ResumeQueue(lambda: resumes, lease_seconds=60, max_attempts=3, backoff_seconds=10, clock=clock)


def add_resume(resumes, minutes=0):
    resume_id = ObjectId()
    resumes.insert_one(
        {
            "_id": resume_id,
            "filename": "cv.pdf",
            "file_path": "cv.pdf",
            "upload_status": "pending",
            "created_at": START + timedelta(minutes=minutes),
        }
    )

    return str(resume_id)


def document(resumes, resume_id):
    return resumes.find_one({"_id": ObjectId(resume_id)})


class ScriptedPipeline:
    """Raises the scripted errors one per call, then returns a usable result."""

    def __init__(self, errors=()):
        self.errors = list(errors)
        self.calls = 0

    def process_pdf(self, path):
        self.calls += 1

        if self.errors:
            raise self.errors.pop(0)

        return {"raw_text": LONG_TEXT, "skills": ["python"]}


def make_service(monkeypatch, resumes, pipeline):
    service = ResumeService.__new__(ResumeService)
    service.resume_pipeline = pipeline
    service.saved = []
    service._build_candidate = lambda resume_id, extracted_data: SimpleNamespace()
    service._save_candidate = lambda candidate: service.saved.append(candidate)
    monkeypatch.setattr(ResumeService, "resumes_col", property(lambda self: resumes))

    return service


def make_worker(queue, service, **options):
    return ResumeWorker(queue, service.process_resume, name="test", **options)


def test_a_waiting_resume_is_processed_and_indexed(monkeypatch, resumes, queue):
    service = make_service(monkeypatch, resumes, ScriptedPipeline())
    resume_id = add_resume(resumes)

    assert make_worker(queue, service).run_once() is True

    saved = document(resumes, resume_id)
    assert saved["upload_status"] == "processed"
    assert "lease_expires" not in saved and "worker_id" not in saved
    assert len(service.saved) == 1


def test_an_empty_queue_is_not_work(monkeypatch, resumes, queue):
    service = make_service(monkeypatch, resumes, ScriptedPipeline())

    assert make_worker(queue, service).run_once() is False


def test_a_temporary_failure_is_retried_later_and_then_succeeds(monkeypatch, resumes, queue, clock):
    pipeline = ScriptedPipeline([RuntimeError("model hiccup")])
    service = make_service(monkeypatch, resumes, pipeline)
    resume_id = add_resume(resumes)
    worker = make_worker(queue, service)

    worker.run_once()

    waiting = document(resumes, resume_id)
    assert waiting["upload_status"] == "pending"
    assert waiting["attempts"] == 1
    assert worker.run_once() is False  # still inside the delay

    clock.now += timedelta(seconds=11)
    worker.run_once()

    assert document(resumes, resume_id)["upload_status"] == "processed"
    assert pipeline.calls == 2


def test_a_resume_that_always_fails_ends_failed_after_the_last_attempt(monkeypatch, resumes, queue, clock):
    pipeline = ScriptedPipeline([RuntimeError("1"), RuntimeError("2"), RuntimeError("3")])
    service = make_service(monkeypatch, resumes, pipeline)
    resume_id = add_resume(resumes)
    worker = make_worker(queue, service)

    for _ in range(3):
        worker.run_once()
        clock.now += timedelta(minutes=10)

    final = document(resumes, resume_id)
    assert final["upload_status"] == "failed"
    assert final["status_reason"] == "processing_error"
    assert final["attempts"] == 3
    assert pipeline.calls == 3
    assert worker.run_once() is False


def test_a_damaged_file_fails_at_once_without_retries(monkeypatch, resumes, queue):
    pipeline = ScriptedPipeline([FileDataError("broken")])
    service = make_service(monkeypatch, resumes, pipeline)
    resume_id = add_resume(resumes)

    make_worker(queue, service).run_once()

    final = document(resumes, resume_id)
    assert (final["upload_status"], final["status_reason"]) == ("failed", "unreadable_file")
    assert final["attempts"] == 1


def test_a_resume_left_processing_by_a_crash_is_taken_again(monkeypatch, resumes, queue, clock):
    service = make_service(monkeypatch, resumes, ScriptedPipeline())
    resume_id = add_resume(resumes)
    queue.claim("dead-worker")  # claimed, then the process died

    worker = make_worker(queue, service)
    assert worker.run_once() is False

    clock.now += timedelta(seconds=61)
    assert worker.run_once() is True
    assert document(resumes, resume_id)["upload_status"] == "processed"


def test_the_lease_is_renewed_while_a_long_resume_is_processed(resumes):
    queue = ResumeQueue(lambda: resumes, lease_seconds=3, max_attempts=3)
    add_resume(resumes)
    renewed = threading.Event()
    original = queue.renew

    def renew(*args):
        renewed.set()

        return original(*args)

    queue.renew = renew

    def slow(resume_id, retry_possible):
        assert renewed.wait(timeout=5), "the lease was not renewed"

    ResumeWorker(queue, slow, name="t").run_once()


def test_started_workers_drain_the_queue_and_stop_cleanly(monkeypatch, resumes, queue):
    service = make_service(monkeypatch, resumes, ScriptedPipeline())
    ids = [add_resume(resumes, minutes=i) for i in range(5)]
    worker = make_worker(queue, service, concurrency=2, poll_seconds=0.05, shutdown_seconds=5)

    worker.start()
    assert worker.alive

    deadline = time.monotonic() + 10

    while time.monotonic() < deadline and any(
        document(resumes, i)["upload_status"] != "processed" for i in ids
    ):
        time.sleep(0.05)

    worker.stop()

    assert all(document(resumes, i)["upload_status"] == "processed" for i in ids)
    assert not worker.alive


def test_the_loop_survives_a_failing_queue():
    class Broken:
        lease_seconds = 60
        calls = 0

        def claim(self, worker_id):
            Broken.calls += 1
            raise RuntimeError("database down")

    worker = ResumeWorker(Broken(), lambda *_: None, poll_seconds=0.01, shutdown_seconds=2)

    worker.start()
    time.sleep(0.2)
    alive = worker.alive
    worker.stop()

    assert alive and Broken.calls > 1


def test_metrics_count_the_outcomes(monkeypatch, resumes, queue):
    from app.core.observability.metrics import RESUME_JOBS

    before = RESUME_JOBS.labels("processed")._value.get()
    service = make_service(monkeypatch, resumes, ScriptedPipeline())
    add_resume(resumes)

    make_worker(queue, service).run_once()

    assert RESUME_JOBS.labels("processed")._value.get() == before + 1
