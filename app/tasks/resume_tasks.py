from __future__ import annotations

from loguru import logger

from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
from app.services.resume_processing_service import (
    ResumeProcessingService,
)


def process_resume_task(
    resume_id: str,
) -> None:

    logger.info(
        "Background resume task started: {}",
        resume_id,
    )

    try:
        pipeline = ResumePipeline()

        processing_service = ResumeProcessingService(
            resume_pipeline=pipeline,
        )

        processing_service.process_pending_resume(
            resume_id=resume_id,
        )

        logger.success(
            "Background resume task completed: {}",
            resume_id,
        )

    except Exception:
        logger.exception(
            "Background resume task failed: {}",
            resume_id,
        )

        raise