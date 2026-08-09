import re
from typing import List, Dict, Any

from loguru import logger


class ExperienceExtractor:
    DATE_RANGE_PATTERN = re.compile(
        r"(?P<start>"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        r"\s+\d{4}"
        r")"
        r"\s*[-–—]\s*"
        r"(?P<end>"
        r"(?:"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        r"\s+\d{4}"
        r"|Present"
        r"|Current"
        r")"
        r")",
        re.IGNORECASE,
    )

    @staticmethod
    def _clean_line(line: str) -> str:
        return line.strip().lstrip("•*-–—").strip()

    @staticmethod
    def _is_date_range(line: str) -> bool:
        return bool(
            ExperienceExtractor.DATE_RANGE_PATTERN.fullmatch(
                line.strip()
            )
        )

    @staticmethod
    def _is_description_line(line: str) -> bool:
        return line.lstrip().startswith(("•", "-", "*"))

    @classmethod
    def _non_empty_lines(cls, text: str) -> List[str]:
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]


    @classmethod
    def _extract_description(
        cls,
        lines: List[str],
    ) -> str:
        description_lines = []

        for line in lines:
            if cls._is_description_line(line):
                cleaned = cls._clean_line(line)

                if cleaned:
                    description_lines.append(cleaned)

        return " ".join(description_lines)

    @classmethod
    def extract(
        cls,
        text: str,
    ) -> List[Dict[str, Any]]:
        if not text:
            return []

        logger.debug(
            "Starting experience extraction."
        )

        lines = cls._non_empty_lines(text)

        experiences: List[Dict[str, Any]] = []

        date_indexes = [
            index
            for index, line in enumerate(lines)
            if cls._is_date_range(line)
        ]

        if not date_indexes:
            logger.debug(
                "No experience date ranges found."
            )
            return []

        for position, date_index in enumerate(date_indexes):
            match = cls.DATE_RANGE_PATTERN.fullmatch(
                lines[date_index]
            )

            if not match:
                continue

            block_end = (
                date_indexes[position + 1]
                if position + 1 < len(date_indexes)
                else len(lines)
            )

            block = lines[date_index + 1:block_end]

            if not block:
                continue

            company = None
            role = None

            # The line immediately before the date range
            # is normally the company.
            if date_index > 0:
                company = lines[date_index - 1]

            # The first non-description line after the date
            # is normally the role.
            for line in block:
                if not line.startswith(("•", "-", "*")):
                    role = line
                    break

            description = cls._extract_description(block)

            experiences.append(
                {
                    "role": role,
                    "company": company,
                    "start_date": match.group("start"),
                    "end_date": match.group("end"),
                    "description": description,
                }
            )

        logger.debug(
            f"Extracted {len(experiences)} experience records."
        )

        return experiences