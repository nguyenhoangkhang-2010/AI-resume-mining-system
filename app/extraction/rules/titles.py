"""
Vocabulary that tells a job title from an employer, and a school from a
degree. It is a hint for splitting a line like "Staff Nurse - St Mary
Hospital", never a list of valid titles: a line the vocabulary cannot split
is left to the language model.
"""

import re
from typing import Iterable, Tuple

from app.extraction.section.heading_lexicon import normalise

ROLE_WORDS = frozenset(
    """
    engineer developer programmer manager analyst nurse teacher accountant
    intern assistant specialist director lead officer consultant designer
    architect administrator coordinator supervisor technician executive
    representative scientist researcher instructor lecturer auditor advisor
    adviser head chief president associate trainee founder tester qa sre
    devops secretary clerk cashier salesperson marketer writer editor
    producer operator mechanic physician doctor surgeon pharmacist therapist
    tutor professor planner buyer agent recruiter controller strategist
    ceo cto cfo coo vp owner partner
    """.split()
)

ROLE_PHRASES = (
    "ky su", "lap trinh vien", "lap trinh", "chuyen vien", "quan ly",
    "truong phong", "truong nhom", "giam doc", "nhan vien", "dieu duong",
    "giao vien", "ke toan", "thuc tap", "tro ly", "giang vien", "tu van",
    "bac si", "duoc si", "chuyen gia", "phien dich", "kiem toan",
    "ky thuat vien", "giam sat", "cong tac vien", "thu ky", "quan tri",
    "tro giang", "dieu phoi",
)

COMPANY_WORDS = frozenset(
    """
    inc ltd llc corp corporation company group bank hospital clinic
    school university college labs lab systems software solutions agency
    studio technologies technology partners capital insurance institute
    centre center foundation industries works consulting holdings
    analytics ventures
    """.split()
)

# "truong" is left out on purpose: it means "school" but also "head of"
# (trưởng phòng, trưởng nhóm), which are job titles.
COMPANY_PHRASES = (
    "cong ty", "tap doan", "ngan hang", "benh vien", "phong kham",
    "trung tam",
)

INSTITUTION_WORDS = frozenset(
    "university college institute school academy polytechnic universite".split()
)

INSTITUTION_PHRASES = (
    "dai hoc", "hoc vien", "truong", "cao dang", "trung tam dao tao",
)

DEGREE_WORDS = frozenset(
    """
    bsc ba bs be beng bachelor bachelors master masters msc ma ms mba meng
    med bed mphil phd doctorate doctoral diploma associate degree gcse
    """.split()
)

DEGREE_PHRASES = (
    "cu nhan", "ky su", "thac si", "tien si", "cao dang", "trung cap",
    "bang cap",
)


def _contains(words: Iterable[str], phrases: Iterable[str], text: str) -> bool:
    normalised = normalise(text)
    tokens = set(normalised.split())

    if any(word in tokens for word in words):
        return True

    padded = f" {normalised} "

    return any(f" {phrase} " in padded for phrase in phrases)


def role_score(text: str) -> int:
    return int(_contains(ROLE_WORDS, ROLE_PHRASES, text))


def company_score(text: str) -> int:
    return int(_contains(COMPANY_WORDS, COMPANY_PHRASES, text))


def is_institution(text: str) -> bool:
    return _contains(INSTITUTION_WORDS, INSTITUTION_PHRASES, text)


def is_degree(text: str) -> bool:
    return _contains(DEGREE_WORDS, DEGREE_PHRASES, text)


_SEPARATORS = (" | ", " - ", " – ", " — ", " @ ", " at ", " tại ", ", ")


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
