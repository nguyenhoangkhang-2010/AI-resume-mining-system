from pathlib import Path
from typing import Dict, Any
import json

from loguru import logger

from app.resume_processing.parsers.pdf_parser import PDFParser
from app.resume_processing.cleaners.text_cleaner import TextCleaner
from app.extraction.section.section_detector import SectionDetector
from app.extraction.extraction_engine import ExtractionEngine
from app.core.config.settings import settings


class ResumePipeline:
    def __init__(self):
        self.parser = PDFParser()
        self.cleaner = TextCleaner()
        
        # Load rules and initialize detectors/engines
        rules_path = Path("app/extraction/config/extraction_rules.json")
        if not rules_path.exists():
            raise FileNotFoundError(f"Extraction rules file not found at {rules_path}")
        with open(rules_path, "r") as f:
            rules = json.load(f)
            
        self.section_detector = SectionDetector(rules)
        self.extraction_engine = ExtractionEngine()

    def process_pdf(
        self,
        file_path: str | Path
    ) -> Dict[str, Any]:
        logger.info(f"Initiating resume processing pipeline for: {file_path}")
        try:
            raw_text = self.parser.extract_text(
                file_path
            )
            cleaned_text = self.cleaner.clean(
                raw_text
            )

            # Step 1: Detect sections from the cleaned text
            sections = self.section_detector.detect(cleaned_text)

            logger.info(f"Detected sections: {list(sections.keys())}")

            for section_name, section_lines in sections.items():
                logger.info(
                    f"\n===== SECTION: {section_name} =====\n"
                    + "\n".join(section_lines[:20])
                )

            # Step 2: Pass the detected sections to the extraction engine
            extracted_data = self.extraction_engine.extract_resume(sections)

            resume_data = {
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                **extracted_data
            }
            
            logger.info("Resume extraction pipeline completed.")
            return resume_data
        except Exception as e:
            logger.error(f"Resume pipeline failed for '{file_path}': {e}")
            raise