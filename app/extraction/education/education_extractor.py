import re
from typing import List, Dict, Any

from loguru import logger


class EducationExtractor:
    DEGREE_PATTERNS = {
        "Bachelor": 
            r"\b(bachelor(?:'s)?|b\.?s\.?|b\.?a\.?|bsc)\b",
        "Master":
            r"\b(master(?:'s)?|m\.?s\.?|m\.?a\.?|msc|mba)\b",
        "Doctorate":
            r"\b(ph\.?d\.?|doctorate)\b"
    }
    
    
    @staticmethod
    def extract(
        text: str
    ) -> List[Dict[str, Any]]:
        if not text:
            return []
        logger.debug(
            "Starting education degree extraction."
        )
        text_lower = text.lower()
        found_degrees = []
        for degree, pattern in (
            EducationExtractor.DEGREE_PATTERNS.items()
        ):
            if re.search(
                pattern,
                text_lower
            ):
                found_degrees.append(
                    degree
                )
        if not found_degrees:
            return []
        result = [
            {
                "degree_level": found_degrees
            }
        ]
        logger.debug(
            f"Extracted degrees: {found_degrees}"
        )
        return result