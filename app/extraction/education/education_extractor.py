import re
from datetime import datetime
from typing import List, Dict, Any

from loguru import logger


class EducationExtractor:

    DEGREE_PATTERNS = {
        "Bachelor": r"\b(bachelor(?:'s)?|b\.?s\.?|b\.?a\.?|bsc)\b",
        "Master": r"\b(master(?:'s)?|m\.?s\.?|m\.?a\.?|msc|mba)\b",
        "Doctorate": r"\b(ph\.?d\.?|doctorate)\b",
    }

    GPA_PATTERN = (
        r"\b(?:gpa|grade point average)"
        r"\s*[:\-]?\s*"
        r"(\d(?:\.\d{1,2})?)"
    )

    YEAR_PATTERN = r"\b(19\d{2}|20\d{2})\b"

    PRESENT_PATTERN = re.compile(
        r"\b(?:present|current|now)\b",
        re.IGNORECASE,
    )

    DATE_RANGE_PATTERN = re.compile(
        r"(?P<start>"
        r"(?:"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        r"\s+"
        r")?"
        r"(19\d{2}|20\d{2})"
        r")"
        r"\s*[-\u2013\u2014]\s*"
        r"(?P<end>"
        r"(?:"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        r"\s+"
        r")?"
        r"(19\d{2}|20\d{2})"
        r"|present"
        r"|current"
        r"|now"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def extract(
        cls,
        text: str,
    ) -> List[Dict[str, Any]]:

        if not text:
            return []

        logger.debug(
            "Starting education extraction."
        )

        lines = cls._non_empty_lines(text)

        result: Dict[str, Any] = {}

        institution = cls._extract_institution(lines)

        if institution:
            result["institution"] = institution

        degree_level = cls._extract_degree_level(text)

        if degree_level:
            result["degree_level"] = degree_level

        gpa = cls._extract_gpa(text)

        if gpa is not None:
            result["gpa"] = gpa

        start_year, end_year = cls._extract_years(text)

        if start_year is not None:
            result["start_year"] = start_year

        if end_year is not None:
            result["end_year"] = end_year

        if not result:
            return []

        logger.debug(
            f"Education extracted: {result}"
        )

        return [result]

    @staticmethod
    def _non_empty_lines(
        text: str,
    ) -> List[str]:

        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    @classmethod
    def _extract_degree_level(
        cls,
        text: str,
    ) -> List[str]:

        text_lower = text.lower()

        degrees = []

        for degree, pattern in cls.DEGREE_PATTERNS.items():
            if re.search(
                pattern,
                text_lower,
            ):
                degrees.append(degree)

        return degrees

    @classmethod
    def _extract_gpa(
        cls,
        text: str,
    ) -> float | None:

        match = re.search(
            cls.GPA_PATTERN,
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        return float(
            match.group(1)
        )

    @classmethod
    def _extract_years(
        cls,
        text: str,
    ) -> tuple[int | None, int | None]:

        current_year = datetime.now().year

        date_range = cls.DATE_RANGE_PATTERN.search(
            text
        )

        if date_range:

            start_value = date_range.group("start")
            end_value = date_range.group("end")

            start_year_match = re.search(
                r"(19\d{2}|20\d{2})",
                start_value,
            )

            end_year_match = re.search(
                r"(19\d{2}|20\d{2})",
                end_value,
            )

            start_year = (
                int(start_year_match.group(1))
                if start_year_match
                else None
            )

            if end_value.lower() in {
                "present",
                "current",
                "now",
            }:
                end_year = current_year

            elif end_year_match:
                end_year = int(
                    end_year_match.group(1)
                )

            else:
                end_year = current_year

            return start_year, end_year

        years = [
            int(year)
            for year in re.findall(
                cls.YEAR_PATTERN,
                text,
            )
        ]

        has_present = bool(
            cls.PRESENT_PATTERN.search(text)
        )

        if len(years) >= 2:

            start_year = years[0]

            if has_present:
                return start_year, current_year

            return start_year, years[1]

        if len(years) == 1:

            if has_present:
                return years[0], current_year

            return None, years[0]

        if has_present:
            return None, current_year

        return None, None

    @classmethod
    def _extract_institution(
        cls,
        lines: List[str],
    ) -> str | None:

        for index, line in enumerate(lines):

            if not cls.DATE_RANGE_PATTERN.fullmatch(
                line
            ):
                continue

            if index == 0:
                return None

            candidate = lines[index - 1].strip()

            if cls._looks_like_non_institution(
                candidate
            ):
                continue

            return candidate

        return None

    @classmethod
    def _looks_like_non_institution(
        cls,
        line: str,
    ) -> bool:

        if not line:
            return True

        if cls.DATE_RANGE_PATTERN.fullmatch(line):
            return True

        if re.search(
            cls.GPA_PATTERN,
            line,
            re.IGNORECASE,
        ):
            return True

        if cls.PRESENT_PATTERN.search(line):
            return True

        for pattern in cls.DEGREE_PATTERNS.values():
            if re.search(
                pattern,
                line,
                re.IGNORECASE,
            ):
                return True

        return False