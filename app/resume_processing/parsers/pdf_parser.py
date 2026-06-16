import fitz
from loguru import logger
from pathlib import Path


class PDFParser:
    
    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        path_obj = Path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            logger.error(f"PDF file not found at path: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.debug(f"Starting text extraction for PDF: {path_obj.name}")
        raw_text = []
        
        try:
            with fitz.open(path_obj) as doc:
                for page_num, page in enumerate(doc):
                    text = page.get_text("text")
                    raw_text.append(text)
            logger.debug(f"Successfully extracted text from {len(raw_text)} pages.")
            return "\n".join(raw_text)
        except Exception as e:
            logger.error(f"Error while parsing PDF '{path_obj.name}': {e}")
            raise