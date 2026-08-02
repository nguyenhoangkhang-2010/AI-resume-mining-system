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

    def __init__(self):

        self.parser = JobDescriptionParser()

        self.extractor = JobExtractor()

    def process(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:

        if file_path is None:
            raise ValueError(
                "file_path cannot be None."
            )

        logger.info(
            f"Starting job pipeline: {file_path}"
        )

        try:
            text = self.parser.parse(
                file_path
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

        logger.info(
            "Job extraction finished successfully."
        )

        logger.success(
            "Job processing completed."
        )

        return result