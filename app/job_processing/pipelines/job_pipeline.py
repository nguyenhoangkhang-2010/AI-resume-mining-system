from pathlib import Path
from typing import Any, Dict

from loguru import logger

from app.resume_processing.cleaners.text_cleaner import TextCleaner
from app.extraction.extraction_engine import ExtractionEngine


class JobPipeline:
    """
    Orchestrates the processing of a Job Description (JD)
    from raw text to structured data.
    """

    def __init__(self):
        self.cleaner = TextCleaner()
        self.extraction_engine = ExtractionEngine()

    def process_job_description(self, raw_text: str) -> Dict[str, Any]:
        logger.info("Initiating job description processing pipeline.")
        try:
            cleaned_text = self.cleaner.clean(raw_text)
            
            # Use LLM for structured extraction of job details
            job_data = self.extraction_engine.extract_job_description(cleaned_text)
            
            # Add raw and cleaned text to the extracted data for completeness
            job_data["raw_text"] = raw_text
            job_data["cleaned_text"] = cleaned_text

            logger.info("Job description extraction pipeline completed.")
            return job_data
        except Exception as e:
            logger.error(f"Job description pipeline failed: {e}")
            raise