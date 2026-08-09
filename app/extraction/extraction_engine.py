from typing import Any, Dict, List

from app.extraction.education.education_extractor import EducationExtractor
from app.extraction.experience.experience_extractor import ExperienceExtractor
from app.extraction.skills.skill_extractor import SkillExtractor
from app.extraction.summary.summary_extractor import SummaryExtractor
from app.extraction.projects.project_extractor import ProjectExtractor
from app.extraction.certifications.certification_extractor import (
    CertificationExtractor,
)
from app.extraction.personal.personal_extractor import PersonalExtractor


class ExtractionEngine:

    def __init__(self) -> None:
        self.extractors = {
            "personal_info": PersonalExtractor(),
            "summary": SummaryExtractor(),
            "education": EducationExtractor(),
            "experience": ExperienceExtractor(),
            "projects": ProjectExtractor(),
            "certifications": CertificationExtractor(),
            "skills": SkillExtractor(),
        }

    def extract_resume(
        self,
        sections: Dict[str, List[str]],
    ) -> Dict[str, Any]:

        section_texts = {
            key: "\n".join(value)
            for key, value in sections.items()
        }

        full_text = "\n".join(
            section_texts.values()
        )

        extracted_data: Dict[str, Any] = {}

        for section_name, extractor in self.extractors.items():

            text = section_texts.get(
                section_name,
                "",
            )

            if not text and section_name in {
                "personal_info",
                "skills",
            }:
                text = full_text

            extracted_data[section_name] = extractor.extract(
                text
            )

        return extracted_data