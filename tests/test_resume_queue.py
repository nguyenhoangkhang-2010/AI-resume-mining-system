from datetime import datetime, timedelta

import mongomock
import pytest
from bson import ObjectId

from app.workers.resume_queue import FAILED, PENDING, PROCESSING, TOO_MANY_ATTEMPTS, ResumeQueue

START = datetime(2026, 1, 1, 12, 0, 0)


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def collection():
    return mongomock.MongoClient().db["resumes"]


@pytest.fixture
def queue(collection, clock):
    return ResumeQueue(
        lambda: collection,
        lease_seconds=60,
        max_attempts=3,
        backoff_seconds=10,
        clock=clock,
    )


def add(collection, minutes=0, **fields):
    document = {
        "_id": ObjectId(),
        "upload_status": PENDING,
        "created_at": START + timedelta(minutes=minutes),
        **fields,
    }
    collection.insert_one(document)

    return str(document["_id"])


def status_of(collection, resume_id):
    return collection.find_one({"_id": ObjectId(resume_id)})


def test_an_empty_queue_gives_nothing(queue):
    assert queue.claim("w1") is None


def test_the_oldest_resume_is_taken_first_and_marked_processing(queue, collection):
    newer = add(collection, minutes=5)
    older = add(collection, minutes=1)

    claim = queue.claim("w1")

    assert claim.resume_id == older
    assert (claim.attempt, claim.max_attempts) == (1, 3)

    document = status_of(collection, older)
    assert document["upload_status"] == PROCESSING
    assert document["worker_id"] == "w1"
    assert document["lease_expires"] == START + timedelta(seconds=60)
    assert status_of(collection, newer)["upload_status"] == PENDING


def test_two_workers_never_take_the_same_resume(queue, collection):
    add(collection, minutes=1)
    add(collection, minutes=2)

    first = queue.claim("w1")
    second = queue.claim("w2")

    assert first.resume_id != second.resume_id
    assert queue.claim("w3") is None


def test_a_resume_being_processed_is_left_alone_until_its_lease_runs_out(queue, collection, clock):
    resume_id = add(collection)
    queue.claim("w1")

    clock.advance(59)
    assert queue.claim("w2") is None

    clock.advance(2)
    again = queue.claim("w2")

    assert again.resume_id == resume_id
    assert again.attempt == 2
    assert status_of(collection, resume_id)["worker_id"] == "w2"


def test_renewing_keeps_the_lease(queue, collection, clock):
    resume_id = add(collection)
    queue.claim("w1")

    clock.advance(50)
    assert queue.renew(resume_id, "w1") is True

    clock.advance(50)
    assert queue.claim("w2") is None


def test_a_worker_that_lost_its_lease_cannot_renew(queue, collection, clock):
    resume_id = add(collection)
    queue.claim("w1")
    clock.advance(120)
    queue.claim("w2")

    assert queue.renew(resume_id, "w1") is False


def test_retry_puts_the_resume_back_after_a_growing_delay(queue, collection, clock):
    resume_id = add(collection)
    claim = queue.claim("w1")

    queue.retry_later(resume_id, "w1", claim.attempt)

    document = status_of(collection, resume_id)
    assert document["upload_status"] == PENDING
    assert "worker_id" not in document and "lease_expires" not in document
    assert queue.claim("w2") is None

    clock.advance(9)
    assert queue.claim("w2") is None

    clock.advance(2)
    second = queue.claim("w2")
    assert second.attempt == 2

    queue.retry_later(resume_id, "w2", second.attempt)
    clock.advance(15)
    assert queue.claim("w3") is None  # the second delay is 20 s

    clock.advance(6)
    assert queue.claim("w3").attempt == 3


def test_a_resume_that_keeps_killing_its_worker_is_given_up_on(queue, collection, clock):
    resume_id = add(collection)

    for _ in range(3):
        assert queue.claim("w").resume_id == resume_id
        clock.advance(61)  # the worker died; the lease ran out

    assert queue.claim("w") is None

    document = status_of(collection, resume_id)
    assert document["upload_status"] == FAILED
    assert document["status_reason"] == TOO_MANY_ATTEMPTS


def test_failing_a_resume_records_the_reason(queue, collection):
    resume_id = add(collection)
    queue.claim("w1")

    queue.fail(resume_id, "unreadable_file")

    document = status_of(collection, resume_id)
    assert (document["upload_status"], document["status_reason"]) == (FAILED, "unreadable_file")
    assert queue.claim("w2") is None


def test_resumes_in_other_states_are_never_claimed(queue, collection):
    for state in ("processed", "needs_review", "failed"):
        add(collection, upload_status=state)

    assert queue.claim("w1") is None


def test_documents_from_before_the_queue_existed_are_picked_up(queue, collection):
    """No attempts, available_at or lease fields, as written by the old code."""

    stuck = add(collection, upload_status=PROCESSING)

    assert queue.claim("w1").resume_id == stuck


def test_stats_count_the_queue_and_the_age_of_the_oldest(queue, collection, clock):
    add(collection, minutes=0)
    add(collection, minutes=2)
    add(collection, minutes=3)
    queue.claim("w1")

    clock.advance(600)
    stats = queue.stats()

    assert (stats.pending, stats.processing) == (2, 1)
    assert stats.oldest_pending_seconds == pytest.approx(600 - 120)


def test_the_age_is_zero_when_nothing_waits(queue):
    assert queue.stats().oldest_pending_seconds == 0.0


def test_at_least_one_attempt_is_required(collection):
    with pytest.raises(ValueError):
        ResumeQueue(lambda: collection, max_attempts=0)
