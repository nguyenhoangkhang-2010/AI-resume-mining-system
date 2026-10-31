"""
Builds the resume processing stack (models, pipeline, service), the queue
worker and the start-up warm-up for the API (`app.main`).
"""

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config.settings import settings
from app.database.mongodb.connection import mongo_db
from app.extraction.extraction_engine import ExtractionEngine
from app.extraction.llm.llm_extractor import LLMExtractor
from app.extraction.section.heading_cache import HeadingCache
from app.extraction.section.heading_classifier import HeadingClassifier
from app.extraction.section.section_classifier import SectionClassifier
from app.extraction.section.section_detector import SectionDetector
from app.extraction.section.section_semantic_classifier import (
    SectionSemanticClassifier,
)
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
from app.services.resume_service import ResumeService
from app.workers.resume_queue import ResumeQueue
from app.workers.resume_worker import ResumeWorker


@dataclass
class ProcessingStack:
    llm_extractor: LLMExtractor
    section_classifier: SectionClassifier
    semantic_classifier: SectionSemanticClassifier
    section_detector: SectionDetector
    extraction_engine: ExtractionEngine
    resume_pipeline: ResumePipeline
    resume_service: ResumeService

    def state(self) -> dict[str, Any]:
        """The attributes the API keeps on `app.state`."""

        return dict(self.__dict__)


def build_processing_stack() -> ProcessingStack:
    llm_extractor = LLMExtractor()
    section_classifier = SectionClassifier(llm_extractor=llm_extractor)
    semantic_classifier = SectionSemanticClassifier()

    section_detector = SectionDetector(
        semantic_classifier=semantic_classifier,
        llm_classifier=section_classifier,
        heading_classifier=HeadingClassifier(),
        heading_cache=HeadingCache(Path(settings.HEADING_CACHE_PATH)),
    )

    extraction_engine = ExtractionEngine(llm_extractor=llm_extractor)

    resume_pipeline = ResumePipeline(
        section_detector=section_detector,
        extraction_engine=extraction_engine,
    )

    return ProcessingStack(
        llm_extractor=llm_extractor,
        section_classifier=section_classifier,
        semantic_classifier=semantic_classifier,
        section_detector=section_detector,
        extraction_engine=extraction_engine,
        resume_pipeline=resume_pipeline,
        resume_service=ResumeService(resume_pipeline=resume_pipeline),
    )


def build_queue() -> ResumeQueue:
    return ResumeQueue(
        lambda: mongo_db.get_db()["resumes"],
        lease_seconds=settings.WORKER_LEASE_SECONDS,
        max_attempts=settings.WORKER_MAX_ATTEMPTS,
        backoff_seconds=settings.WORKER_RETRY_BACKOFF_SECONDS,
    )


def build_worker(service: ResumeService, queue: ResumeQueue) -> ResumeWorker:
    logger.info(
        "Resume worker: concurrency {}, lease {}s, up to {} attempts.",
        settings.WORKER_CONCURRENCY,
        settings.WORKER_LEASE_SECONDS,
        settings.WORKER_MAX_ATTEMPTS,
    )

    return ResumeWorker(
        queue,
        service.process_resume,
        concurrency=settings.WORKER_CONCURRENCY,
        poll_seconds=settings.WORKER_POLL_SECONDS,
        shutdown_seconds=settings.WORKER_SHUTDOWN_SECONDS,
    )


def warm_up() -> None:
    """
    Builds the services that are otherwise built by the first request that
    needs them. On the development CPU the first call to the jobs endpoints
    took about 70 seconds (the occupation taxonomy and the job models load),
    which a client would see as a timeout.
    """

    from app.api.dependencies.job import (
        get_job_recommendation_service,
        get_job_service,
    )
    from app.embeddings.services.embedding_service import EmbeddingService

    started = time.perf_counter()

    EmbeddingService().generate_embedding("warm up")
    get_job_service()
    get_job_recommendation_service()

    logger.info("Warm-up finished in {:.1f}s.", time.perf_counter() - started)


def start_warm_up(state: Any) -> threading.Thread:
    """
    Runs the warm-up on a thread and sets `state.warm` when it is done, so
    the API starts answering at once and /ready says when it is fully ready.
    A failure is logged and does not block readiness: the services are still
    built by the first request, as before.
    """

    state.warm = False

    def run() -> None:
        try:
            warm_up()
        except Exception:
            logger.exception("Warm-up failed; services will load on first use.")
        finally:
            state.warm = True

    thread = threading.Thread(target=run, name="warm-up", daemon=True)
    thread.start()

    return thread
