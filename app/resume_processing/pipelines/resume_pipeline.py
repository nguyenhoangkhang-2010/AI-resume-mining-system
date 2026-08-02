from pathlib import Path
from typing import Dict, Any

from loguru import logger

from app.resume_processing.parsers.pdf_parser import PDFParser
from app.resume_processing.cleaners.text_cleaner import TextCleaner


from app.extraction.contact.contact_extractor import ContactExtractor
from app.extraction.summary.summary_extractor import SummaryExtractor
from app.extraction.education.education_extractor import EducationExtractor
from app.extraction.experience.experience_extractor import ExperienceExtractor
from app.extraction.projects.project_extractor import ProjectExtractor
from app.extraction.certifications.certification_extractor import CertificationExtractor
from app.extraction.skills.skill_extractor import SkillExtractor



class ResumePipeline:


    def __init__(self):

        self.parser = PDFParser()
        self.cleaner = TextCleaner()
        self.contact_extractor = ContactExtractor()
        self.summary_extractor = SummaryExtractor()
        self.education_extractor = EducationExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.project_extractor = ProjectExtractor()
        self.certification_extractor = CertificationExtractor()
        self.skill_extractor = SkillExtractor()


    def process_pdf(
        self,
        file_path: str | Path
    ) -> Dict[str, Any]:
        logger.info(
            f"Initiating resume processing pipeline for: {file_path}"
        )
        try:
            raw_text = self.parser.extract_text(
                file_path
            )
            cleaned_text = self.cleaner.clean(
                raw_text
            )
            resume_data = {
                "contact":
                    self.contact_extractor.extract(
                        cleaned_text
                    ),
                "summary":
                    self.summary_extractor.extract(
                        cleaned_text
                    ),
                "education":
                    self.education_extractor.extract(
                        cleaned_text
                    ),
                "experience":
                    self.experience_extractor.extract(
                        cleaned_text
                    ),
                "projects":
                    self.project_extractor.extract(
                        cleaned_text
                    ),
                "certifications":
                    self.certification_extractor.extract(
                        cleaned_text
                    ),
                "skills":
                    self.skill_extractor.extract(
                        cleaned_text
                    )
            }
            logger.info(
                "Resume extraction pipeline completed."
            )
            return resume_data
        except Exception as e:
            logger.error(
                f"Resume pipeline failed for '{file_path}': {e}"
            )
            raise