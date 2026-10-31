"""
Reads the experience section of a CV without the language model, when its
layout is regular enough to do so reliably.

Each job in a typical CV has a date range, a few header lines near it (the
title, the employer, perhaps a place) and bullet points. The date ranges mark
where jobs are. The header lines are the short non-bullet lines just before and
just after a date range; each one is typed as a title, an employer or a place
from the vocabulary files, and a job is understood when exactly one title and
one employer (or just one of them) come out and nothing is left over.

The parser answers only when every job it finds is understood. If anything is
unclear (no date ranges, header lines it cannot type, text before the first
job) it raises Unclear and the caller asks the language model, so a CV with an
unusual layout is no worse off than before.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from app.extraction.rules.dates import DateRange, find_range
from app.extraction.rules.titles import (
    company_score,
    ends_with_company_suffix,
    is_location,
    order_role_company,
    role_score,
    split_location,
    split_pair,
)

# Characters that start a bullet point, as opposed to a sentence.
_BULLET_CHARS = "-•*▪●◦·–—⋄◆◇■□►▶❖✓✔∙‣⁃○◉➢➤★☆→"
BULLET = re.compile(rf"^\s*(?:[{re.escape(_BULLET_CHARS)}]|\d{{1,2}}[.)](?=\s))\s*")
_EDGE_SEPARATORS = " \t|,;:-–—"

MAX_HEADER_WORDS = 12
MAX_HEADER_PARTS = 3
MAX_VALUE_WORDS = 12
HEADER_MARKER_WORDS = 5


class Unclear(Exception):
    """The layout is not understood; `reason` says why (for logs and stats)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _is_bullet(line: str) -> bool:
    return bool(BULLET.match(line)) and not line.strip()[:1].isalpha()


def _is_header_like(line: str) -> bool:
    text = line.strip()

    if not text or _is_bullet(text) or find_range(text):
        return False

    if len(text.split()) > MAX_HEADER_WORDS or re.search(r":\s*\S", text):
        return False

    if text.endswith((".", ";")) and not _may_end_with_stop(text):
        return False

    first_letter = next((c for c in text if c.isalpha()), "")

    return not first_letter or first_letter.isupper()


def _may_end_with_stop(text: str) -> bool:
    """A full stop that belongs to the name: "Acme Ltd." or "Acme (France)."."""

    stripped = text.rstrip(".;")

    return stripped.endswith(")") or ends_with_company_suffix(stripped)


def _clean_value(text: str) -> str:
    cleaned = " ".join(text.strip(_EDGE_SEPARATORS).split())

    if cleaned.endswith(".") and not ends_with_company_suffix(cleaned):
        cleaned = cleaned.rstrip(".").strip()

    return cleaned


# ------------------------------------------------------------ bullet markers


def _header_markers(lines: List[str], anchors: List[int]) -> Set[str]:
    """
    Marker characters that introduce employer names rather than descriptions.

    Some CVs mark each employer with one symbol ("• Google") and each duty
    with another ("◦ Built ..."). A marker is a header marker when every line
    that carries it is short, it is used at least twice, no two of its lines
    follow each other (duties come in runs, employers do not), and every one
    of its lines sits just above a date range. Anything less certain leaves
    the symbol a bullet, and a section that then starts with one is left to the
    model.
    """

    by_marker: Dict[str, List[int]] = {}

    for index, line in enumerate(lines):
        if _is_bullet(line):
            by_marker.setdefault(line.strip()[0], []).append(index)

    markers = set()

    for marker, indexes in by_marker.items():
        if len(indexes) < 2:
            continue

        texts = [BULLET.sub("", lines[i], count=1) for i in indexes]

        if any(len(t.split()) > HEADER_MARKER_WORDS or re.search(r"[.:;]", t) for t in texts):
            continue

        if any(later - earlier == 1 for earlier, later in zip(indexes, indexes[1:])):
            continue

        near = sum(any(0 < a - i <= MAX_HEADER_PARTS + 1 for a in anchors) for i in indexes)

        if near == len(indexes):
            markers.add(marker)

    return markers


# ----------------------------------------------------------- reading a header


@dataclass
class Header:
    role: Optional[str]
    company: Optional[str]
    location: Optional[str]


def _type_of(text: str) -> str:
    role, company = role_score(text), company_score(text)

    if role > company:
        return "role"

    if company > role:
        return "company"

    return "unknown"


def _read_header(parts: List[str]) -> Optional[Header]:
    """Role, company and place out of the header lines of one job, or None."""

    location: Optional[str] = None
    names: List[str] = []

    for part in parts:
        text = _clean_value(part)

        if not text:
            continue

        if is_location(text):
            location = location or text
            continue

        text, place = split_location(text)
        location = location or place
        text = _clean_value(text)

        if text:
            names.append(text)

    if not names or any(len(name.split()) > MAX_VALUE_WORDS for name in names):
        return None

    if len(names) == 1:
        return _read_single(names[0], location)

    # A line holding both ("Backend Engineer - Acme") cannot share the header.
    if any(_complete_pair(name) is not None for name in names):
        return None

    kinds = [_type_of(name) for name in names]
    roles = [n for n, k in zip(names, kinds) if k == "role"]
    companies = [n for n, k in zip(names, kinds) if k == "company"]
    unknown = [n for n, k in zip(names, kinds) if k == "unknown"]

    if len(roles) > 1 or len(companies) > 1:
        return None

    if roles and companies and not unknown:
        return Header(roles[0], companies[0], location)

    if len(unknown) == 1 and (roles or companies) and len(roles) + len(companies) == 1:
        if roles:
            return Header(roles[0], unknown[0], location)

        return Header(unknown[0], companies[0], location)

    return None


def _complete_pair(text: str) -> Optional[Tuple[str, str]]:
    """(role, company) when one line holds both and the vocabulary can tell which is which."""

    pair = split_pair(text)
    ordered = order_role_company(*pair) if pair else None

    # An employer word on one side is not enough to call the other a title
    # ("Big Bank Plc - Head Office"): the title side needs a title word.
    return ordered if ordered and role_score(ordered[0]) > 0 else None


def _read_single(text: str, location: Optional[str]) -> Optional[Header]:
    ordered = _complete_pair(text)

    if ordered:
        return Header(_clean_value(ordered[0]), _clean_value(ordered[1]), location)

    if split_pair(text):
        # Two parts the vocabulary cannot tell apart ("BAT - British American
        # Tobacco"): guessing which is the employer would be wrong half the time.
        return None

    if _type_of(text) == "role":
        return Header(text, None, location)

    return Header(None, text, location)


# -------------------------------------------------------------------- jobs


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

    # A symbol that marks employers is not a bullet.
    for marker in _header_markers(lines, anchors):
        lines = [
            BULLET.sub("", line, count=1) if _is_bullet(line) and line.strip()[0] == marker else line
            for line in lines
        ]

    ranges: Dict[int, DateRange] = {
        index: date for index in anchors if (date := find_range(lines[index]))
    }

    before = {anchor: _lines_before(lines, anchor, anchors, ranges) for anchor in anchors}
    claimed = {index for indexes in before.values() for index in indexes}
    after = {anchor: _lines_after(lines, anchor, anchors, claimed) for anchor in anchors}

    jobs: List[Dict[str, Any]] = []
    starts: List[int] = []
    ends: List[int] = []

    for anchor in anchors:
        positions = [*before[anchor], anchor, *after[anchor]]
        parts = [lines[i] for i in positions if i != anchor]

        if ranges[anchor].rest:
            parts.insert(len(before[anchor]), ranges[anchor].rest)

        header = _read_header(parts)

        if header is None or not (header.role or header.company):
            raise Unclear("role and company not told apart")

        starts.append(positions[0])
        ends.append(positions[-1])

        dates = ranges[anchor]
        jobs.append(
            {
                "company": header.company,
                "role": header.role,
                "start_date": dates.start,
                "end_date": dates.end,
                "description": [],
                "employment_type": None,
                "location": header.location,
                "achievements": [],
            }
        )

    if starts[0] > 0:
        raise Unclear("text before the first job")

    for position, job in enumerate(jobs):
        following = starts[position + 1] if position + 1 < len(jobs) else len(lines)
        job["description"] = _description(lines[ends[position] + 1: following])

    return jobs


def _looks_like_header_line(lines: List[str], index: int) -> bool:
    """
    A header-like line right under a bullet could be the wrapped end of that
    bullet; it counts as a header only if it carries some sign of one.
    """

    text = lines[index]

    if index == 0 or not (_is_bullet(lines[index - 1]) or lines[index - 1] == ""):
        return True

    return bool(
        role_score(text)
        or company_score(text)
        or is_location(text)
        or split_pair(text)
        or ends_with_company_suffix(text)
    )


def _lines_before(
    lines: List[str],
    anchor: int,
    anchors: List[int],
    ranges: Dict[int, DateRange],
) -> List[int]:
    previous = max((a for a in anchors if a < anchor), default=-1)
    found: List[int] = []
    index = anchor - 1

    while (
        index > previous
        and len(found) < MAX_HEADER_PARTS
        and _is_header_like(lines[index])
        and index not in ranges
    ):
        if not _looks_like_header_line(lines, index):
            break

        found.insert(0, index)
        index -= 1

    return found


def _lines_after(
    lines: List[str],
    anchor: int,
    anchors: List[int],
    claimed: Set[int],
) -> List[int]:
    found: List[int] = []
    index = anchor + 1

    while (
        index < len(lines)
        and len(found) < MAX_HEADER_PARTS
        and index not in claimed
        and index not in anchors
        and _is_header_like(lines[index])
    ):
        found.append(index)
        index += 1

    return found
