import re
from typing import List, Dict, Any
from loguru import logger


class ExperienceExtractor:
    YEARS_OF_EXP_PATTERN = r"(\d+)\+?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience|exp)"
    
    @staticmethod
    def extract(text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        logger.debug("Starting experience extraction.")
        text_lower = text.lower()
        experience_info = []
        
        years_matches = re.findall(ExperienceExtractor.YEARS_OF_EXP_PATTERN, text_lower)
        total_years = 0
        
        if years_matches:
            total_years = max([int(y) for y in years_matches])
            
        experience_info.append({
            "total_years_extracted": total_years
        })
        
        logger.debug(f"Extracted {total_years} years of experience.")
        return experience_info