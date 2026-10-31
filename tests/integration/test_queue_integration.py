import threading
from datetime import datetime

import pytest

from app.workers.resume_queue import ResumeQueue


def test_concurrent_workers_never_claim_the_same_resume(database):
    resumes = database["resumes"]
    resumes.insert_many(
        [
            {"upload_status": "pending", "created_at": datetime(2026, 1, 1, 12, 0, i)}
            for i in range(40)
        ]
    )
    queue = ResumeQueue(lambda: resumes)
    claimed: list = []
    lock = threading.Lock()

    def work(name):
        while True:
            claim = queue.claim(name)

            if claim is None:
                return

            with lock:
                claimed.append(claim.resume_id)

    threads = [threading.Thread(target=work, args=(f"w{i}",)) for i in range(8)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=30)

    assert len(claimed) == 40
    assert len(set(claimed)) == 40


def test_the_status_and_created_index_exists(database):
    from app.database.mongodb.indexes import ensure_indexes

    assert ensure_indexes(database) == []
    assert "upload_status_created" in database["resumes"].index_information()


@pytest.mark.parametrize("state", ["processed", "failed", "needs_review"])
def test_finished_resumes_are_not_claimed(database, state):
    database["resumes"].insert_one(
        {"upload_status": state, "created_at": datetime(2026, 1, 1)}
    )

    assert ResumeQueue(lambda: database["resumes"]).claim("w") is None
