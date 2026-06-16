from pathlib import Path
from loguru import logger

from app.resume_processing.parsers.pdf_parser import PDFParser
from app.resume_processing.cleaners.text_cleaner import TextCleaner


class ResumePipeline:    
    def __init__(self):
        self.parser = PDFParser()
        self.cleaner = TextCleaner()

    def process_pdf(self, file_path: str | Path) -> str:
        logger.info(f"Initiating resume processing pipeline for: {file_path}")
        
        try:
            raw_text = self.parser.extract_text(file_path)
            
            cleaned_text = self.cleaner.clean(raw_text)
            return cleaned_text
        except Exception as e:
            logger.error(f"Resume pipeline failed for '{file_path}': {e}")
            raise