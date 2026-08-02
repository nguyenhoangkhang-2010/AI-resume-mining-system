import re
from typing import List, Dict, Any

from loguru import logger


class ExperienceExtractor:

    YEARS_PATTERN = (
        r"(\d+)"
        r"\+?\s*"
        r"(years|yrs)"
        r"\s*(of)?"
        r"\s*(experience|exp)"
    )


    RANGE_PATTERN = (
        r"(\d{4})"
        r"\s*-\s*"
        r"(\d{4}|present)"
    )


    @staticmethod
    def extract(
        text: str
    ) -> List[Dict[str, Any]]:
        if not text:
            return []
        logger.debug(
            "Starting experience extraction."
        )
        text_lower = text.lower()
        result = {
            "total_years_extracted": 0,
            "experience_periods": []
        }
        # Extract explicit years experience
        years_matches = re.findall(
            ExperienceExtractor.YEARS_PATTERN,
            text_lower
        )
        if years_matches:
            result["total_years_extracted"] = max(
                int(year[0])
                for year in years_matches
            )
        # Extract working periods
        periods = re.findall(
            ExperienceExtractor.RANGE_PATTERN,
            text_lower
        )
        for start, end in periods:
            result["experience_periods"].append(
                {
                    "start": start,
                    "end": end
                }
            )
        logger.debug(
            f"Experience extracted: {result}"
        )
        return [
            result
        ]