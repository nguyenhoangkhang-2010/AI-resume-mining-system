"""
Reads the experience section of a CV without the language model, when its
layout is regular enough to do so reliably.

Each job in a typical CV has a date range, a title/employer header next to
it and bullet points below. The date ranges mark where jobs start; the
header lines beside each range hold the role and the company; the lines
under it are the description. This is what the language model was being
asked to do at about a minute per CV.

The parser answers only when every job it finds is fully understood. If
anything is unclear (no date ranges, a header it cannot split into role and
company, text before the first job) it returns None and the caller asks the
model, so a CV with an unusual layout is no worse off than before.
"""

import re
from typing import Any, Dict, List, Optional

from app.extraction.rules.dates import DateRange, find_range
from app.extraction.rules.titles import (
    company_score,
    order_role_company,
    role_score,
    split_pair,
)

BULLET = re.compile(r"^\s*(?:[-•*▪●◦·–—]|\d{1,2}[.)])\s*")
_EDGE_SEPARATORS = " \t|,;:-–—"

MAX_HEADER_WORDS = 12
MAX_HEADER_LINES = 2


def _is_bullet(line: str) -> bool:
    return bool(BULLET.match(line)) and not line.strip()[:1].isalpha()


def _is_header_like(line: str) -> bool:
    text = line.strip()

    if not text or _is_bullet(text) or find_range(text):
        return False

    if text.endswith((".", ";")) or len(text.split()) > MAX_HEADER_WORDS:
        return False

    first_letter = next((c for c in text if c.isalpha()), "")

    return not first_letter or first_letter.isupper()


def _clean_header(text: str) -> str:
    return " ".join(text.strip(_EDGE_SEPARATORS).split())


def _role_and_company(parts: List[str]) -> Optional[Dict[str, Optional[str]]]:
    parts = [_clean_header(part) for part in parts if _clean_header(part)]

    if len(parts) == 1:
        pair = split_pair(parts[0])

        if pair:
            ordered = order_role_company(*pair)

            if ordered is None:
                return None

            return {"role": ordered[0], "company": ordered[1]}

        if role_score(parts[0]) > company_score(parts[0]):
            return {"role": parts[0], "company": None}

        return {"role": None, "company": parts[0]}

    if len(parts) == 2:
        ordered = order_role_company(parts[0], parts[1])

        if ordered is None:
            return None

        return {"role": ordered[0], "company": ordered[1]}

    return None


def _description(lines: List[str]) -> List[str]:
    """Bullets, with wrapped continuation lines joined to their bullet."""

    items: List[str] = []

    for line in lines:
        text = line.strip()

        if _is_bullet(text):
            items.append(BULLET.sub("", text, count=1).strip())
            continue

        continues = bool(items) and (
            text[:1].islower() or not items[-1].endswith((".", ";", ":"))
        )

        if continues:
            items[-1] = f"{items[-1]} {text}"
        else:
            items.append(text)

    return [item for item in items if item]


class Unclear(Exception):
    """The layout is not understood; `reason` says why (for logs and stats)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def parse_experience(text: str) -> Optional[List[Dict[str, Any]]]:
    """The jobs in the section, or None when the layout is not understood."""

    try:
        return read_experience(text)
    except Unclear:
        return None


def explain_experience(text: str) -> str:
    """Why parse_experience gives up on this text ("" when it does not)."""

    try:
        read_experience(text)
    except Unclear as unclear:
        return unclear.reason

    return ""


def read_experience(text: str) -> List[Dict[str, Any]]:
    """The jobs in the section; raises Unclear when the layout is not understood."""

    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]

    anchors = [
        index
        for index, line in enumerate(lines)
        if not _is_bullet(line) and find_range(line) is not None
    ]

    if not anchors:
        raise Unclear("no date range")

    ranges: Dict[int, DateRange] = {
        index: date for index in anchors if (date := find_range(lines[index]))
    }

    header_first = _header_precedes(lines, anchors)

    spans = []  # (first line of the job, last line of its header/date block)
    headers: List[List[str]] = []

    for position, anchor in enumerate(anchors):
        previous_anchor = anchors[position - 1] if position else -1
        parts = [ranges[anchor].rest] if ranges[anchor].rest else []
        first = last = anchor

        step = -1 if header_first else 1
        index = anchor + step
        limit = previous_anchor if header_first else len(lines)

        while (
            (index > limit if header_first else index < limit)
            and len(parts) < MAX_HEADER_LINES
            and _is_header_like(lines[index])
            and index not in ranges
        ):
            if not _complete_header(parts) and not _plausible_header(lines[index], parts):
                raise Unclear("header unclear")

            if header_first:
                parts.insert(0, lines[index])
                first = index
            else:
                parts.append(lines[index])
                last = index

            index += step

            if _complete_header(parts):
                break

        # A third header line cannot be told from the job's description.
        if (
            (index > limit if header_first else index < limit)
            and not _complete_header(parts)
            and _is_header_like(lines[index])
            and index not in ranges
        ):
            raise Unclear("header of three lines")

        spans.append((first, last))
        headers.append(parts)

    if spans[0][0] > 0:
        raise Unclear("text before the first job")

    jobs: List[Dict[str, Any]] = []

    for position, (_, last) in enumerate(spans):
        following = spans[position + 1][0] if position + 1 < len(spans) else len(lines)
        names = _role_and_company(headers[position])

        if names is None or not (names["role"] or names["company"]):
            raise Unclear("role and company not told apart")

        dates = ranges[anchors[position]]

        jobs.append(
            {
                "company": names["company"],
                "role": names["role"],
                "start_date": dates.start,
                "end_date": dates.end,
                "description": _description(lines[last + 1: following]),
                "employment_type": None,
                "location": None,
                "achievements": [],
            }
        )

    return jobs


def _complete_header(parts: List[str]) -> bool:
    """True when the header lines so far already give a role and a company."""

    cleaned = [_clean_header(part) for part in parts if _clean_header(part)]

    if len(cleaned) == 2:
        return order_role_company(cleaned[0], cleaned[1]) is not None

    if len(cleaned) == 1:
        pair = split_pair(cleaned[0])

        return pair is not None and order_role_company(*pair) is not None

    return False


def _plausible_header(line: str, parts: List[str]) -> bool:
    """A line that can be part of a header: it has title/employer words or a split."""

    if not parts:
        return True

    return role_score(line) > 0 or company_score(line) > 0 or split_pair(line) is not None


def _header_precedes(lines: List[str], anchors: List[int]) -> bool:
    """True for "header, dates, bullets"; False for "dates, header, bullets"."""

    first = anchors[0]
    before = first > 0 and _is_header_like(lines[first - 1])
    after = first + 1 < len(lines) and _is_header_like(lines[first + 1])

    if before:
        return True

    return not after
