"""
Reads the education section of a CV without the language model, when each
school line is clear (see experience_rules.py for the approach).

A school is a line with an institution word (university, college, đại
học ...). The degree, the years and the GPA sit on the lines next to it. If
a line cannot be assigned, or a school is found without a clear degree/year
layout around it, the parser returns None and the model is asked.
"""

import re
from typing import Any, Dict, List, Optional

from app.extraction.rules.dates import find_range, year_of
from app.extraction.rules.experience_rules import BULLET
from app.extraction.rules.titles import is_degree, is_institution, split_pair

MAX_LINE_WORDS = 14

_GPA = re.compile(
    r"(?:gpa|cgpa|diem\s*tb|điểm\s*(?:trung\s*bình|tb))\s*[:=\-]?\s*"
    r"(\d{1,2}(?:[.,]\d{1,2})?)(?:\s*/\s*\d{1,2}(?:[.,]\d)?)?",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def _is_school_line(line: str) -> bool:
    return (
        not BULLET.match(line)
        and len(line.split()) <= MAX_LINE_WORDS
        and is_institution(line)
    )


def _years(lines: List[str]) -> tuple[Optional[int], Optional[int]]:
    for line in lines:
        found = find_range(line)

        if found:
            start = year_of(found.start)
            end = None if not _YEAR.search(found.end) else year_of(found.end)

            return start, end

    singles = [int(year) for line in lines for year in _YEAR.findall(line)]

    if len(singles) >= 2:
        return singles[0], singles[1]

    if len(singles) == 1:
        return None, singles[0]

    return None, None


def _gpa(lines: List[str]) -> Optional[float]:
    for line in lines:
        match = _GPA.search(line)

        if match:
            return float(match.group(1).replace(",", "."))

    return None


def _institution_and_degree(line: str) -> tuple[str, Optional[str]]:
    """Splits "BSc in Nursing, Hanoi Medical University" when it is one line."""

    pair = split_pair(line)

    if pair:
        for school, other in (pair, pair[::-1]):
            if is_institution(school) and not is_institution(other):
                return school, other if is_degree(other) else None

    return line.strip(), None


def parse_education(text: str) -> Optional[List[Dict[str, Any]]]:
    """The education entries, or None when the layout is not understood."""

    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    schools = [index for index, line in enumerate(lines) if _is_school_line(line)]

    if not schools:
        return None

    # Does the degree come before the school ("BSc / University / years")?
    degree_first = schools[0] > 0 and is_degree(lines[schools[0] - 1])

    if schools[0] > 0 and not degree_first:
        extra = lines[: schools[0]]

        if not all(find_range(line) or _YEAR.search(line) for line in extra):
            return None

    entries: List[Dict[str, Any]] = []

    for position, school in enumerate(schools):
        following = schools[position + 1] if position + 1 < len(schools) else len(lines)
        previous = schools[position - 1] if position else -1

        if degree_first:
            # Years and notes after the school belong to it; the lines just
            # before the next school (its degree) do not.
            end = following
            block_after = lines[school + 1: end]
            tail = [
                line
                for line in block_after
                if find_range(line) or _GPA.search(line) or _YEAR.search(line)
            ]
            degree_lines = [
                line for line in lines[max(previous + 1, school - 1): school]
                if is_degree(line)
            ]
            others = tail
        else:
            block = lines[school + 1: following]
            degree_lines = [line for line in block if is_degree(line)]
            others = block

        institution, inline_degree = _institution_and_degree(lines[school])

        if inline_degree:
            degree_lines = [inline_degree, *degree_lines]

        start, end_year = _years(others + [lines[school]])

        entries.append(
            {
                "institution": institution,
                "degree_level": degree_lines[:1],
                "start_year": start,
                "end_year": end_year,
                "gpa": _gpa(others),
            }
        )

    return entries
