from pathlib import Path
from typing import Any

from loguru import logger

from app.job_processing.parsers.job_parser import (
    JobDescriptionParser,
)

from app.extraction.job.job_extractor import (
    JobExtractor,
)


class JobPipeline:
    """
    Turns a job description (raw text or a file path) into
    structured data: requirements, responsibilities and skills.
    """

    def __init__(self):

        self.parser = JobDescriptionParser()

        self.extractor = JobExtractor()

    def process(
        self,
        source: str | Path,
    ) -> dict[str, Any]:

        if source is None:
            raise ValueError(
                "source cannot be None."
            )

        logger.info(
            "Starting job pipeline."
        )

        try:
            text = self.parser.parse(
                source
            )
        except Exception as exc:
            logger.exception(
                f"Failed to parse job description: {exc}"
            )
            raise

        if not text or not text.strip():
            logger.warning(
                "Empty job description detected."
            )
            return {
                "requirements": None,
                "responsibilities": None,
                "skills": [],
            }

        logger.info(
            "Extracting job information..."
        )

        result = self.extractor.extract(text)

        logger.success(
            "Job processing completed."
        )

        return result
