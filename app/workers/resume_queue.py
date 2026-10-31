"""
A work queue for CV processing, kept in the `resumes` collection.

Processing a CV takes seconds to minutes on CPU, so it cannot run inside the
request. Until now it ran as a FastAPI background task: if the process
restarted the resume stayed `processing` for ever, a failure was never
retried, and the number of CVs processed at once was whatever the thread pool
allowed. The queue fixes those three things without new infrastructure, using
the database the application already needs:

- a worker *claims* a resume with one atomic update (`pending` -> `processing`
  with a lease), so two workers never take the same CV;
- the lease expires if the worker dies or hangs, and the CV is claimed again;
- a failure that may be temporary is retried with a growing delay, up to a
  maximum number of attempts, then the CV is marked `failed`.

Redis plus Celery or RQ would give the same behaviour with more features
(priorities, rate limits, a dashboard) and one more service to run. This queue
is a few hundred lines, is covered by tests, and is replaceable behind
`claim`/`renew`/`retry_later`/`fail` if the volume ever needs that.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from loguru import logger
from pymongo import ASCENDING, ReturnDocument

PENDING = "pending"
PROCESSING = "processing"
FAILED = "failed"

TOO_MANY_ATTEMPTS = "too_many_attempts"


def utc_now() -> datetime:
    # Naive UTC, like the other timestamps the application stores.
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class Claim:
    resume_id: str
    attempt: int
    max_attempts: int

    @property
    def last_attempt(self) -> bool:
        return self.attempt >= self.max_attempts


@dataclass(frozen=True)
class QueueStats:
    pending: int
    processing: int
    oldest_pending_seconds: float


class ResumeQueue:

    def __init__(
        self,
        collection: Callable[[], Any],
        lease_seconds: int = 600,
        max_attempts: int = 3,
        backoff_seconds: int = 30,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        self._collection = collection
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self._clock = clock

    @property
    def collection(self) -> Any:
        return self._collection()

    def claim(self, worker_id: str) -> Optional[Claim]:
        """
        Takes the oldest resume that is waiting (or whose worker's lease ran
        out), or returns None. A resume that has already been taken the
        maximum number of times is failed instead of being tried again: a CV
        that kills its worker every time must not keep killing workers.
        """

        while True:
            now = self._clock()

            document = self.collection.find_one_and_update(
                {
                    "$or": [
                        {
                            "upload_status": PENDING,
                            "$or": [
                                {"available_at": {"$exists": False}},
                                {"available_at": {"$lte": now}},
                            ],
                        },
                        {
                            "upload_status": PROCESSING,
                            "$or": [
                                {"lease_expires": {"$exists": False}},
                                {"lease_expires": {"$lt": now}},
                            ],
                        },
                    ]
                },
                {
                    "$set": {
                        "upload_status": PROCESSING,
                        "worker_id": worker_id,
                        "lease_expires": now + timedelta(seconds=self.lease_seconds),
                        "started_at": now,
                    },
                    "$inc": {"attempts": 1},
                },
                sort=[("created_at", ASCENDING)],
                return_document=ReturnDocument.AFTER,
            )

            if document is None:
                return None

            resume_id = str(document["_id"])
            attempt = int(document.get("attempts", 1))

            if attempt > self.max_attempts:
                logger.error(
                    "Resume {} was taken {} times without finishing; giving up.",
                    resume_id,
                    attempt - 1,
                )
                self._mark_failed(document["_id"], TOO_MANY_ATTEMPTS)
                continue

            return Claim(resume_id, attempt, self.max_attempts)

    def renew(self, resume_id: Any, worker_id: str) -> bool:
        """Extends the lease while the worker is still busy; False if it was lost."""

        result = self.collection.update_one(
            {"_id": self._object_id(resume_id), "worker_id": worker_id, "upload_status": PROCESSING},
            {"$set": {"lease_expires": self._clock() + timedelta(seconds=self.lease_seconds)}},
        )

        return result.matched_count == 1

    def retry_later(self, resume_id: Any, worker_id: str, attempt: int) -> None:
        """Puts the resume back in the queue after a delay that doubles with each attempt."""

        delay = self.backoff_seconds * (2 ** max(0, attempt - 1))

        self.collection.update_one(
            {"_id": self._object_id(resume_id), "worker_id": worker_id},
            {
                "$set": {
                    "upload_status": PENDING,
                    "available_at": self._clock() + timedelta(seconds=delay),
                },
                "$unset": {"lease_expires": "", "worker_id": ""},
            },
        )

    def fail(self, resume_id: Any, reason: str) -> None:
        self._mark_failed(self._object_id(resume_id), reason)

    def stats(self) -> QueueStats:
        now = self._clock()
        pending = self.collection.count_documents({"upload_status": PENDING})
        processing = self.collection.count_documents({"upload_status": PROCESSING})

        oldest = self.collection.find_one(
            {"upload_status": PENDING},
            sort=[("created_at", ASCENDING)],
            projection={"created_at": 1},
        )
        created = oldest.get("created_at") if oldest else None
        age = (now - created).total_seconds() if isinstance(created, datetime) else 0.0

        return QueueStats(pending, processing, max(0.0, age))

    def _mark_failed(self, document_id: Any, reason: str) -> None:
        self.collection.update_one(
            {"_id": document_id},
            {
                "$set": {"upload_status": FAILED, "status_reason": reason},
                "$unset": {"lease_expires": "", "worker_id": ""},
            },
        )

    @staticmethod
    def _object_id(resume_id: Any) -> Any:
        if isinstance(resume_id, str):
            from bson import ObjectId

            return ObjectId(resume_id)

        return resume_id
