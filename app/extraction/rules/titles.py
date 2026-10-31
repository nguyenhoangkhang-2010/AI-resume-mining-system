"""
Tells a job title from an employer, a school from a degree, and a place from
either, using the vocabulary files (see vocabulary.py).

This is a hint for reading a line such as "Staff Nurse - St Mary Hospital",
never a list of valid titles: a line the vocabulary cannot place is left to the
language model.
"""

import re
from typing import Optional, Tuple

from app.extraction.rules.vocabulary import get_vocabulary
from app.extraction.section.heading_lexicon import normalise

_SEPARATORS = (" | ", " - ", " – ", " — ", " @ ", " at ", " tại ", ", ")

# "Mountain View, CA"  "Georgetown, TX": a place name and a two-letter state.
_CITY_STATE = re.compile(r"^[^\W\d_][\w .'’-]*,\s*[A-Z]{2}\.?$")

_TRAILING_PARENTHESIS = re.compile(r"^(?P<name>.*?)\s*\((?P<inside>[^()]*)\)\W*$")


def role_score(text: str) -> int:
    """How many job-title words or phrases the text contains."""

    return get_vocabulary().roles.count(text)


def company_score(text: str) -> int:
    """How many employer words or phrases the text contains."""

    return get_vocabulary().companies.count(text)


def is_institution(text: str) -> bool:
    return get_vocabulary().institutions.count(text) > 0


def is_degree(text: str) -> bool:
    return get_vocabulary().degrees.count(text) > 0


def is_location(text: str) -> bool:
    """A line that is only a place: "Mountain View, CA", "Hanoi, Vietnam", "Remote"."""

    stripped = text.strip().rstrip(".")

    if not stripped or len(stripped.split()) > 8 or any(c.isdigit() for c in stripped):
        return False

    if _CITY_STATE.match(stripped):
        return True

    places = get_vocabulary().places
    parts = [part.strip() for part in stripped.split(",") if part.strip()]

    # Every comma-separated part is made of known place names, nothing else.
    return bool(parts) and all(places.covers(part) for part in parts)


def split_location(text: str) -> Tuple[str, Optional[str]]:
    """
    "Shockelasrull (Luxembourg)." -> ("Shockelasrull", "Luxembourg"). Other
    parentheses, such as "(BAT)", stay in the name.
    """

    match = _TRAILING_PARENTHESIS.match(text.strip())

    if match and match.group("name") and is_location(match.group("inside")):
        return match.group("name").strip(), match.group("inside").strip()

    return text.strip(), None


def ends_with_company_suffix(text: str) -> bool:
    """"... Ltd." and "... Inc." end with a full stop that belongs to the name."""

    words = normalise(text).split()

    return bool(words) and words[-1] in get_vocabulary().company_suffixes


def split_pair(text: str) -> Tuple[str, str] | None:
    """Splits "A - B" at the first separator, or None if there is none."""

    for separator in _SEPARATORS:
        match = re.search(re.escape(separator), text, re.IGNORECASE)

        if match:
            left = text[: match.start()].strip()
            right = text[match.end():].strip()

            if left and right:
                return left, right

    return None


def order_role_company(first: str, second: str) -> Tuple[str, str] | None:
    """
    Which of two strings is the role and which the company, from their
    words. None when the vocabulary cannot tell.
    """

    first_role, second_role = role_score(first), role_score(second)
    first_company, second_company = company_score(first), company_score(second)

    first_leans_role = (first_role - second_role) + (second_company - first_company)

    if first_leans_role > 0:
        return first, second

    if first_leans_role < 0:
        return second, first

    return None
