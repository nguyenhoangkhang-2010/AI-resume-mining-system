from __future__ import annotations

import re
from typing import Dict, List

from loguru import logger


class ProjectSegmenter:

    DATE_PATTERN = re.compile(
        r"""
        (?:
            \b\d{4}\b
            |
            \b
            (?:
                jan|feb|mar|apr|may|jun|
                jul|aug|sep|sept|oct|nov|dec
            )
            [a-z]*
            \s+
            \d{4}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    DATE_RANGE_PATTERN = re.compile(
        r"""
        (?:
            \b\d{4}\b
            |
            \b
            (?:
                jan|feb|mar|apr|may|jun|
                jul|aug|sep|sept|oct|nov|dec
            )
            [a-z]*
            \s+
            \d{4}
        )
        \s*
        (?:
            -
            |
            –
            |
            —
            |
            to
            |
            until
        )
        \s*
        (?:
            \b\d{4}\b
            |
            \b
            (?:
                jan|feb|mar|apr|may|jun|
                jul|aug|sep|sept|oct|nov|dec
            )
            [a-z]*
            \s+
            \d{4}
            |
            \b(?:present|current|now)
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    SECTION_BOUNDARY_PATTERN = re.compile(
        r"""
        ^
        \s*
        (?:
            honors?
            |
            awards?
            |
            certifications?
            |
            education
            |
            experience
            |
            skills?
            |
            languages?
            |
            references?
            |
            additional\s+information
        )
        \s*
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def __init__(self) -> None:
        pass

    @staticmethod
    def _clean_line(
        line: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            line,
        ).strip()

    @staticmethod
    def _is_bullet(
        line: str,
    ) -> bool:

        return bool(
            re.match(
                r"""
                ^
                \s*
                (?:
                    [-•●▪◦‣*]
                    |
                    \d+[.)]
                )
                \s+
                """,
                line,
                re.VERBOSE,
            )
        )

    @classmethod
    def _contains_date(
        cls,
        line: str,
    ) -> bool:

        return bool(
            cls.DATE_PATTERN.search(line)
        )

    @classmethod
    def _contains_date_range(
        cls,
        line: str,
    ) -> bool:

        return bool(
            cls.DATE_RANGE_PATTERN.search(line)
        )

    @classmethod
    def _is_section_boundary(
        cls,
        line: str,
    ) -> bool:

        return bool(
            cls.SECTION_BOUNDARY_PATTERN.match(
                line
            )
        )

    @classmethod
    def _looks_like_structural_header(
        cls,
        line: str,
    ) -> bool:

        if not line:
            return False

        if cls._is_bullet(line):
            return False

        if len(line) > 220:
            return False

        score = 0

        if cls._contains_date_range(line):
            score += 4

        elif cls._contains_date(line):
            score += 2

        if ":" in line:
            score += 1

        if "|" in line:
            score += 1

        if (
            '"' in line
            or "“" in line
            or "”" in line
        ):
            score += 1

        return score >= 3

    @classmethod
    def _is_candidate_boundary(
        cls,
        lines: List[str],
        index: int,
    ) -> bool:

        line = lines[index]

        if not cls._looks_like_structural_header(
            line
        ):
            return False

        if index == 0:
            return True

        previous = lines[index - 1]

        if cls._looks_like_structural_header(
            previous
        ):
            return False

        return True

    @classmethod
    def _append_segment(
        cls,
        segments: List[Dict[str, str]],
        lines: List[str],
    ) -> None:

        if not lines:
            return

        cleaned = [
            cls._clean_line(line)
            for line in lines
            if line.strip()
        ]

        if not cleaned:
            return

        segments.append(
            {
                "raw_text": "\n".join(
                    cleaned
                ).strip()
            }
        )

    @classmethod
    def segment(
        cls,
        text: str,
    ) -> List[Dict[str, str]]:

        if not text or not text.strip():
            return []

        lines = [
            cls._clean_line(line)
            for line in text.splitlines()
            if line.strip()
        ]

        if not lines:
            return []

        segments: List[Dict[str, str]] = []

        current: List[str] = []

        for index, line in enumerate(lines):

            if cls._is_section_boundary(line):

                if current:
                    cls._append_segment(
                        segments,
                        current,
                    )

                break

            # New project candidate.
            if cls._is_candidate_boundary(
                lines,
                index,
            ):

                if current:
                    cls._append_segment(
                        segments,
                        current,
                    )

                current = [line]

                continue

            if current:
                current.append(line)

            else:
                # Preserve leading content instead of
                # silently dropping it.
                current = [line]

        if current:
            cls._append_segment(
                segments,
                current,
            )

        logger.debug(
            "Project segmentation produced {} candidate segments.",
            len(segments),
        )

        return segments