"""
Worker threads that take resumes from the queue and process them.

`run_once` claims one resume and handles it to the end, which is what the
tests drive; `start` runs that in a loop on `concurrency` threads.
"""

import threading
import time
import uuid
from typing import Callable, List, Optional

from loguru import logger

from app.core.observability.metrics import RESUME_JOB_SECONDS, RESUME_JOBS
from app.services.resume_quality import is_retryable
from app.workers.resume_queue import Claim, ResumeQueue

# process(resume_id, retry_possible): runs the pipeline. It raises on failure.
# When retry_possible is true it leaves a failure that may be temporary
# unrecorded, so the worker can put the resume back in the queue.
ProcessFunction = Callable[[str, bool], None]


class _Lease:
    """Renews the lease of the resume being processed, until stopped."""

    def __init__(self, queue: ResumeQueue, resume_id: str, worker_id: str) -> None:
        self._queue = queue
        self._resume_id = resume_id
        self._worker_id = worker_id
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=f"lease-{resume_id[:8]}",
            daemon=True,
        )

    def __enter__(self) -> "_Lease":
        self._thread.start()

        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _run(self) -> None:
        interval = max(1.0, self._queue.lease_seconds / 3)

        while not self._stop.wait(interval):
            try:
                if not self._queue.renew(self._resume_id, self._worker_id):
                    logger.warning("Lost the lease on resume {}.", self._resume_id)
                    return
            except Exception:
                logger.exception("Could not renew the lease on resume {}.", self._resume_id)


class ResumeWorker:

    def __init__(
        self,
        queue: ResumeQueue,
        process: ProcessFunction,
        concurrency: int = 1,
        poll_seconds: float = 2.0,
        shutdown_seconds: float = 30.0,
        name: Optional[str] = None,
    ) -> None:
        self.queue = queue
        self.process = process
        self.concurrency = max(1, concurrency)
        self.poll_seconds = poll_seconds
        self.shutdown_seconds = shutdown_seconds
        self.name = name or f"worker-{uuid.uuid4().hex[:8]}"
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []

    # ---------------------------------------------------------------- one job

    def run_once(self, worker_id: Optional[str] = None) -> bool:
        """Claims and handles one resume. Returns False if the queue was empty."""

        worker_id = worker_id or self.name
        claim = self.queue.claim(worker_id)

        if claim is None:
            return False

        self._handle(claim, worker_id)

        return True

    def _handle(self, claim: Claim, worker_id: str) -> None:
        started = time.perf_counter()
        outcome = "processed"

        with logger.contextualize(resume_id=claim.resume_id):
            logger.info(
                "Processing resume (attempt {} of {}).",
                claim.attempt,
                claim.max_attempts,
            )

            try:
                with _Lease(self.queue, claim.resume_id, worker_id):
                    self.process(claim.resume_id, not claim.last_attempt)

            except Exception as error:
                if not claim.last_attempt and is_retryable(error):
                    outcome = "retried"
                    self.queue.retry_later(claim.resume_id, worker_id, claim.attempt)
                    logger.warning("Attempt {} failed; the resume will be tried again.", claim.attempt)
                else:
                    outcome = "failed"
                    # process() has recorded the failure when it was not left for a retry.
                    logger.error("Giving up on the resume after attempt {}.", claim.attempt)

            finally:
                RESUME_JOBS.labels(outcome).inc()
                RESUME_JOB_SECONDS.observe(time.perf_counter() - started)

    # ------------------------------------------------------------------- loop

    def start(self) -> None:
        if self._threads:
            return

        self._stop.clear()

        for index in range(self.concurrency):
            thread = threading.Thread(
                target=self._loop,
                args=(f"{self.name}-{index}",),
                name=f"resume-worker-{index}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

        logger.info("Started {} worker thread(s).", self.concurrency)

    def stop(self) -> None:
        """Stops taking new resumes and waits for the current ones, up to the shutdown time."""

        self._stop.set()
        deadline = time.monotonic() + self.shutdown_seconds

        for thread in self._threads:
            thread.join(timeout=max(0.0, deadline - time.monotonic()))

        still_running = [t.name for t in self._threads if t.is_alive()]

        if still_running:
            logger.warning(
                "{} worker thread(s) still busy at shutdown; their resumes are "
                "claimed again when the lease runs out.",
                len(still_running),
            )

        self._threads = []

    @property
    def alive(self) -> bool:
        return bool(self._threads) and all(t.is_alive() for t in self._threads)

    def _loop(self, worker_id: str) -> None:
        while not self._stop.is_set():
            try:
                worked = self.run_once(worker_id)
            except Exception:
                # The queue itself (the database) failed; wait and look again.
                logger.exception("Worker could not read the queue.")
                worked = False

            if not worked:
                self._stop.wait(self.poll_seconds)
