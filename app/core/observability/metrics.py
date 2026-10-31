"""
Prometheus metrics: HTTP traffic, CV processing and the processing queue.

Labels are kept to a few fixed values (the route template, not the URL, so a
resume id never becomes a label) to keep the number of series small.
"""

from typing import Callable, Optional

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests handled.",
    ["method", "route", "status"],
)

HTTP_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Time to answer an HTTP request.",
    ["method", "route"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

RESUME_JOBS = Counter(
    "resume_jobs_total",
    "Resume processing attempts by outcome (processed, needs_review, failed, retried, error).",
    ["outcome"],
)

RESUME_JOB_SECONDS = Histogram(
    "resume_job_duration_seconds",
    "Time to process one resume, from claim to end of the attempt.",
    buckets=(1, 5, 15, 30, 60, 120, 300, 600, 1800),
)

QUEUE_PENDING = Gauge("resume_queue_pending", "Resumes waiting to be processed.")
QUEUE_PROCESSING = Gauge("resume_queue_processing", "Resumes being processed.")
QUEUE_OLDEST = Gauge(
    "resume_queue_oldest_pending_seconds",
    "Age of the oldest resume still waiting.",
)


def watch_queue(read: Callable[[], Optional[object]]) -> None:
    """
    Makes the queue gauges read the queue when Prometheus scrapes. `read`
    returns a QueueStats, or None when the database is not reachable (the
    gauges then report NaN instead of a stale number).
    """

    def value(attribute: str) -> Callable[[], float]:
        def getter() -> float:
            try:
                stats = read()
            except Exception:
                stats = None

            return float(getattr(stats, attribute)) if stats is not None else float("nan")

        return getter

    QUEUE_PENDING.set_function(value("pending"))
    QUEUE_PROCESSING.set_function(value("processing"))
    QUEUE_OLDEST.set_function(value("oldest_pending_seconds"))


def render() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
