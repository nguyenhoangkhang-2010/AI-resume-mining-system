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
            r"\b(ph\.?d\.?|doctorate)\b",
    }


    GPA_PATTERN = (
        r"\b(?:gpa|grade point average)"
        r"\s*[:\-]?\s*"
        r"(\d(?:\.\d{1,2})?)"
    )


    YEAR_PATTERN = (
        r"\b(19\d{2}|20\d{2})\b"
    )


    MAJOR_KEYWORDS = [
        "computer science",
        "information technology",
        "data science",
        "software engineering",
        "artificial intelligence",
        "cyber security",
        "business administration",
    ]


    @staticmethod
    def extract(
        text: str
    ) -> List[Dict[str, Any]]:
        if not text:
            return []
        logger.debug(
            "Starting education extraction."
        )
        text_lower = text.lower()
        result = {}

        # Degree extraction
        degrees = []
        for degree, pattern in (
            EducationExtractor.DEGREE_PATTERNS.items()
        ):
            if re.search(
                pattern,
                text_lower
            ):
                degrees.append(
                    degree
                )
        if degrees:
            result["degree_level"] = degrees

        # Major extraction
        majors = []
        for major in (
            EducationExtractor.MAJOR_KEYWORDS
        ):
            if major in text_lower:
                majors.append(
                    major.title()
                )
        if majors:
            result["major"] = majors

        # GPA extraction
        gpa_match = re.search(
            EducationExtractor.GPA_PATTERN,
            text_lower
        )
        if gpa_match:
            result["gpa"] = float(
                gpa_match.group(1)
            )

        # Graduation year extraction
        years = re.findall(
            EducationExtractor.YEAR_PATTERN,
            text
        )
        if years:
            result["years"] = [
                int(year)
                for year in years
            ]
        if not result:
            return []
        logger.debug(
            f"Education extracted: {result}"
        )
        return [
            result
        ]