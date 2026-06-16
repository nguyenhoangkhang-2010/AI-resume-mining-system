import re
from loguru import logger


class TextCleaner:
    
    @staticmethod
    def clean(raw_text: str) -> str:
        if not raw_text:
            logger.warning("Received empty string for text cleaning.")
            return ""
            
        logger.debug("Starting text cleaning process.")
        
        cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', raw_text)
        
        cleaned_text = re.sub(r'[•●▪■◆]', '-', cleaned_text)
        
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text.strip()