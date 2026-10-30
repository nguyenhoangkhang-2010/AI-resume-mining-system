"""
Certifications and projects without the language model, for sections that
are plain lists (one certificate per line; a title followed by bullets).

Like the other rules, these answer only when every line is accounted for;
anything else (sentences among the titles, a fragment that may be the
wrapped end of the previous line, two titles in a row) returns None and the
model is asked.
"""

import re
from typing import Any, Dict, List, Optional

from app.extraction.rules.dates import find_range
from app.extraction.rules.experience_rules import (
    BULLET,
    _description,
    _is_bullet,
    _is_header_like,
)
from app.extraction.rules.titles import company_score, is_institution, split_pair

MAX_CERTIFICATE_WORDS = 14
# A line this short that follows a longer one is probably its wrapped end.
FRAGMENT_WORDS = 2
FRAGMENT_AFTER_CHARS = 20

_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_URL = re.compile(r"https?://\S+|(?:www\.|github\.com/|gitlab\.com/)\S+", re.IGNORECASE)
_TECH = re.compile(
    r"^(?:tech(?:nolog(?:y|ies))?|tech stack|stack|tools?|built with|"
    r"công nghệ|cong nghe|công cụ)\s*[:：]\s*(?P<items>.+)$",
    re.IGNORECASE,
)


def _lines(text: str) -> List[str]:
    return [" ".join(line.split()) for line in text.splitlines() if line.strip()]


def parse_certifications(text: str) -> Optional[List[Dict[str, Any]]]:
    """One certificate per line, or None when the lines are not clearly that."""

    lines = _lines(text)

    if not lines:
        return None

    names: List[str] = []

    for line in lines:
        body = BULLET.sub("", line, count=1).strip() if _is_bullet(line) else line
        words = body.split()

        if not words or len(words) > MAX_CERTIFICATE_WORDS or body.endswith("."):
            return None

        wrapped_end = (
            len(words) <= FRAGMENT_WORDS
            and bool(names)
            and len(names[-1]) >= FRAGMENT_AFTER_CHARS
            and not _is_bullet(line)
        )

        if wrapped_end:
            return None

        names.append(body)

    return [_certificate(name) for name in names]


def _certificate(line: str) -> Dict[str, Any]:
    year = _YEAR.findall(line)
    link = _URL.search(line)
    found = find_range(line)
    issued = found.start if found else (year[-1] if year else None)

    name = _YEAR.sub("", line)
    name = re.sub(r"[\(\[]\s*[\)\]]", "", name)
    name = " ".join(name.split()).strip(" -–—|,;:()[]")

    issuer = None
    pair = split_pair(name)

    if pair:
        for title, maybe_issuer in (pair, pair[::-1]):
            if (
                is_institution(maybe_issuer) and not is_institution(title)
            ) or company_score(maybe_issuer) > company_score(title):
                name, issuer = title, maybe_issuer
                break

    return {
        "name": name or line,
        "issuer": issuer,
        "issue_date": issued,
        "expiry_date": None,
        "credential_id": None,
        "credential_url": link.group(0) if link else None,
    }


def parse_projects(text: str) -> Optional[List[Dict[str, Any]]]:
    """Titled projects with bullets or a short paragraph, or None when unclear."""

    lines = _lines(text)

    if not lines:
        return None

    projects: List[Dict[str, Any]] = []
    body: List[str] = []
    title: Optional[str] = None

    def close() -> bool:
        nonlocal body, title

        if title is None:
            return not body

        if not body:
            return False

        projects.append(_project(title, body))
        title, body = None, []

        return True

    for line in lines:
        starts_project = _is_header_like(line) and (not body or _ends_body(body))

        if starts_project:
            if title is not None and not body:
                return None  # two titles in a row

            if not close():
                return None

            title = line
            continue

        if title is None:
            return None  # text before the first title

        body.append(line)

    if not close() or not projects:
        return None

    return projects


def _ends_body(body: List[str]) -> bool:
    """A new title can follow the last line of a bullet or a sentence."""

    last = body[-1]

    return _is_bullet(last) or last.endswith(".") or bool(_TECH.match(last))


def _project(title: str, body: List[str]) -> Dict[str, Any]:
    technologies: List[str] = []
    rest: List[str] = []
    dates = None
    url = None

    for line in body:
        tech = _TECH.match(BULLET.sub("", line, count=1).strip())

        if tech:
            technologies += [
                item.strip() for item in re.split(r"[,;/|]", tech.group("items")) if item.strip()
            ]
            continue

        found = find_range(line)

        if dates is None and found and not rest and not _is_bullet(line):
            dates = found
            continue

        link = _URL.search(line)

        if url is None and link:
            url = link.group(0).rstrip(".,)")

        rest.append(line)

    return {
        "title": title,
        "description": _description(rest),
        "start_date": dates.start if dates else None,
        "end_date": dates.end if dates else None,
        "role": None,
        "team_size": None,
        "technologies": technologies,
        "responsibilities": [],
        "achievements": [],
        "url": url,
        "metadata": {},
    }
