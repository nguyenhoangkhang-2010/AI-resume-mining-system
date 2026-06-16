import re
from typing import List, Dict, Any
from loguru import logger


class EducationExtractor:
    DEGREE_PATTERNS = {
        "bachelor": r"\b(bachelor(?:'s)?|b\.?s\.?|b\.?a\.?|bsc)\b",
        "master": r"\b(master(?:'s)?|m\.?s\.?|m\.?a\.?|msc|mba)\b",
        "doctorate": r"\b(ph\.?d\.?|doctorate)\b"
    }
    
    @staticmethod
    def extract(text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        logger.debug("Starting education extraction.")
        text_lower = text.lower()
        education_info = []
        
        found_degrees = []
        for degree_level, pattern in EducationExtractor.DEGREE_PATTERNS.items():
            if re.search(pattern, text_lower):
                found_degrees.append(degree_level.capitalize())
        
        if found_degrees:
            education_info.append({
                "level": found_degrees,
                "details": "Degree level identified from text."
            })
            
        logger.debug(f"Extracted education records: {found_degrees}")
        return education_info