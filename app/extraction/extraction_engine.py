from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from loguru import logger

from app.extraction.certifications.certification_extractor import (
    CertificationExtractor,
)
from app.extraction.education.education_extractor import EducationExtractor
from app.extraction.experience.experience_extractor import ExperienceExtractor
from app.extraction.llm.llm_extractor import LLMExtractor
from app.extraction.ner.ner_service import NERService
from app.extraction.personal.personal_extractor import PersonalExtractor
from app.extraction.projects.project_extractor import ProjectExtractor
from app.extraction.skills.skill_extractor import SkillExtractor
from app.extraction.summary.summary_extractor import SummaryExtractor


class ExtractionEngine:

    def __init__(
        self,
        llm_extractor: LLMExtractor,
    ) -> None:
        logger.info("Initializing extraction engine dependencies.")

        self.llm_extractor = llm_extractor
        self.ner_service = NERService()

        self.extractors = {
            "personal_info": PersonalExtractor(
                ner_service=self.ner_service,
            ),
            "summary": SummaryExtractor(
                self.llm_extractor,
            ),
            "education": EducationExtractor(
                llm_extractor=self.llm_extractor,
            ),
            "experience": ExperienceExtractor(
                self.llm_extractor,
            ),
            "projects": ProjectExtractor(
                llm_extractor=self.llm_extractor,
            ),
            "certifications": CertificationExtractor(
                self.llm_extractor,
            ),
            "skills": SkillExtractor(
                ner_service=self.ner_service,
            ),
        }

        logger.success(
            "Extraction engine initialized successfully."
        )

    def extract_resume(
        self,
        sections: Dict[str, List[str]],
    ) -> Dict[str, Any]:

        if not sections:
            return {}
        
        section_texts = {
            key: "\n".join(value)
            for key, value in sections.items()
            if not key.startswith("__")
        }

        full_text = "\n".join(
            text
            for text in section_texts.values()
            if text
        )

        project_regions = sections.get(
            "__projects_regions__"
        )

        extracted_data: Dict[str, Any] = {}

        for section_name, extractor in self.extractors.items():

            text = section_texts.get(
                section_name,
                "",
            )

            if section_name == "skills":
                text = full_text

            elif not text and section_name == "personal_info":
                text = full_text

            logger.info(
                "========== START EXTRACTOR: {} ==========",
                section_name,
            )

            start_time = time.perf_counter()

            try:
                if section_name == "projects":
                    result = self._extract_projects(
                        extractor=extractor,
                        project_regions=project_regions,
                        fallback_text=text,
                    )
                else:
                    result = extractor.extract(text)

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                logger.success(
                    "Extractor '{}' completed in {:.3f}s",
                    section_name,
                    elapsed,
                )

                extracted_data[section_name] = result

            except Exception:
                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                logger.exception(
                    "Extractor '{}' failed after {:.3f}s",
                    section_name,
                    elapsed,
                )

                raise

        return extracted_data

    @staticmethod
    def _extract_projects(
        extractor: ProjectExtractor,
        project_regions: Optional[List[str]],
        fallback_text: str,
    ) -> List[Dict[str, Any]]:

        regions = (
            project_regions
            if project_regions
            else (
                [fallback_text]
                if fallback_text
                else []
            )
        )

        all_projects: List[Dict[str, Any]] = []

        for region_text in regions:

            if not region_text or not region_text.strip():
                continue

            projects = extractor.extract(
                region_text,
                section_type="projects",
            )

            all_projects.extend(projects)

        return all_projects