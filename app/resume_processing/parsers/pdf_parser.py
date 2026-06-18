import fitz
from loguru import logger
from pathlib import Path


class PDFParser:
    
    @staticmethod
    def extract_text(file_path: str | Path, password: str | None = None) -> str:
        path_obj = Path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            logger.error(f"PDF file not found at path: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.debug(f"Starting text extraction for PDF: {path_obj.name}")
        raw_text = []
        
        try:
            with fitz.open(path_obj) as doc:
                if doc.is_encrypted:
                    logger.warning(f"PDF '{path_obj.name}' is encrypted. Attempting to authenticate.")
                    # PyMuPDF's authenticate returns the number of permissions granted, 0 if failed
                    if not doc.authenticate(password):
                        logger.error(f"Failed to authenticate encrypted PDF '{path_obj.name}'. Invalid or no password provided.")
                        raise ValueError(f"Failed to decrypt PDF '{path_obj.name}'. Password may be incorrect.")

                for page_num, page in enumerate(doc):
                    text = page.get_text("text")
                    raw_text.append(text)
            logger.debug(f"Successfully extracted text from {len(raw_text)} pages.")
            return "\n".join(raw_text)
        except ValueError as ve:
            # Re-raise the password-related error directly
            raise ve
        except Exception as e:
            logger.error(f"Error while parsing PDF '{path_obj.name}': {e}")
            raise