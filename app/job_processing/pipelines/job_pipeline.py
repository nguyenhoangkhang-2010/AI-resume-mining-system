from pathlib import Path
from typing import Any

from loguru import logger

from app.job_processing.parsers.job_parser import (
    JobDescriptionParser,
)

from app.extraction.job.requirement_extractor import (
    RequirementExtractor,
)
from app.extraction.job.responsibility_extractor import (
    ResponsibilityExtractor,
)
from app.extraction.job.job_skill_extractor import (
    JobSkillExtractor,
)


class JobPipeline:

    def __init__(self):

        self.parser = JobDescriptionParser()

        self.skill_extractor = JobSkillExtractor()

    def process(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:

        logger.info(
            f"Starting job pipeline: {file_path}"
        )

        text = self.parser.parse(file_path)

        if not text.strip():
            logger.warning("Empty job description detected.")
            return {
                "requirements": None,
                "responsibilities": None,
                "skills": [],
            }

        logger.info(
            "Extracting job requirements..."
        )
        requirements = RequirementExtractor.extract(
            text
        )

        logger.info(
            "Extracting responsibilities..."
        )
        responsibilities = ResponsibilityExtractor.extract(
            text
        )

        logger.info(
            "Extracting required skills..."
        )
        skills = self.skill_extractor.extract(
            text
        )

        logger.success(
            "Job processing completed."
        )

        return {
            "requirements": requirements,
            "responsibilities": responsibilities,
            "skills": skills,
        }