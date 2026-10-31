"""
Recognises resume section headings from their wording.

Headings are matched on text alone, so they are found whatever the visual
style (uppercase, bold, same size as the body, different colour) and wherever
the PDF puts line breaks. A line counts as a heading only if all of its words
are heading vocabulary, so ordinary body lines such as "Skills in Python and
SQL" are not mistaken for one.

English and Vietnamese are built in; other languages come from the `headings`
key of the vocabulary files (app/extraction/rules/vocabulary/). Words are
matched without diacritics ("Kinh nghiệm" and "Kinh nghiem" are the same),
which also covers text extracted with broken accents.
"""

import re
import unicodedata
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

MAX_HEADING_CHARS = 70
MAX_HEADING_WORDS = 8
MAX_PHRASE_WORDS = 5

# Section name -> normalised heading phrases (no diacritics, lowercase).
# Catch-all headings ("Additional Information") are deliberately absent:
# what they hold differs from CV to CV (often the skills), so the text
# under them decides, not the heading.
HEADING_PHRASES: Dict[str, Sequence[str]] = {
    "personal_info": (
        "contact", "contacts", "contact information", "contact details",
        "personal information", "personal details", "personal info",
        "personal data",
        "thong tin ca nhan", "thong tin lien he", "lien he",
    ),
    "summary": (
        "summary", "career summary", "executive summary", "profile summary",
        "personal profile", "career profile", "objective",
        "career objective", "objectives", "profile", "about", "about me",
        "introduction", "overview",
        "muc tieu", "muc tieu nghe nghiep", "gioi thieu",
        "gioi thieu ban than", "tom tat", "tong quan", "ve toi",
    ),
    "experience": (
        "experience", "experiences", "work experience", "working experience",
        "employment", "employment history", "work history", "career history",
        "job history", "industry experience",
        "internship", "internships", "internship experience",
        "volunteer", "volunteering", "volunteer experience", "activities",
        "extracurricular activities", "leadership",
        "kinh nghiem", "kinh nghiem lam viec", "kinh nghiem chuyen mon",
        "kinh nghiem thuc tap", "qua trinh lam viec", "qua trinh cong tac",
        "cong viec", "lich su lam viec", "thuc tap", "hoat dong",
        "hoat dong ngoai khoa", "hoat dong xa hoi",
    ),
    "education": (
        "education", "education details", "educational qualifications",
        "academic history", "degrees", "educational background",
        "education background",
        "academic background", "academic", "studies", "education and training",
        "hoc van", "trinh do hoc van", "qua trinh hoc tap", "hoc tap",
        "dao tao", "hoc van va dao tao", "thong tin hoc van",
    ),
    "skills": (
        "skills", "skill", "skill set", "key skills", "core skills",
        "hard skills", "soft skills", "skills summary",
        "competencies", "core competencies", "expertise", "technologies",
        "tools", "tech stack", "programming languages", "skills and tools",
        "ky nang", "ky nang chuyen mon", "ky nang mem", "ky nang cung",
        "cong nghe", "cong cu", "chuyen mon", "nang luc",
    ),
    "projects": (
        "projects", "project", "personal projects", "academic projects",
        "side projects", "portfolio", "project experience",
        "project highlights", "open source", "open source contributions",
        "du an", "du an ca nhan", "du an noi bat", "du an da tham gia",
    ),
    "certifications": (
        "certifications", "certification", "certificates", "certificate",
        "licenses", "licences", "licenses and certifications", "credentials",
        "courses", "training", "trainings", "scholarships", "awards",
        "honors", "honours", "achievements", "accomplishments",
        "chung chi", "giai thuong", "thanh tich", "khoa hoc",
    ),
    "other": (
        "references", "reference", "interests", "hobbies",
        "interests and hobbies", "languages",
        "so thich", "nguoi tham chieu", "ngoai ngu",
    ),
}

# Qualifiers and connectives that may surround a heading phrase.
FILLER_WORDS = frozenset(
    {
        "my", "the", "a", "and", "va", "of", "other", "additional",
        "relevant", "related", "key", "main", "selected", "notable",
        "professional", "technical", "detailed", "brief", "general",
    }
)

_NUMBERING = re.compile(r"^\s*(?:\d{1,2}|[ivxlc]{1,4})\s*[.)\-:]\s+", re.IGNORECASE)


def normalise(text: str) -> str:
    """
    Lowercase, strip diacritics (including Vietnamese đ) and punctuation.

    Letters of other scripts (Cyrillic, Greek, Arabic, CJK ...) are kept as
    they are: only the accents of Latin letters are removed, because in
    those scripts a combining mark can be part of the letter.
    """

    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)

    kept: List[str] = []

    for char in text.casefold():
        if unicodedata.category(char).startswith("M"):
            if kept and _is_latin(kept[-1]):
                continue

            kept.append(char)
        else:
            kept.append(char if char.isalnum() else " ")

    return " ".join("".join(kept).split())


def _is_latin(char: str) -> bool:
    return char.isascii() or unicodedata.name(char, "").startswith("LATIN")


@lru_cache(maxsize=1)
def _phrase_index() -> Dict[str, str]:
    """The built-in phrases (English, Vietnamese) plus those of vocabulary files."""

    from app.extraction.rules.vocabulary import get_vocabulary

    index: Dict[str, str] = {}

    for section, phrases in HEADING_PHRASES.items():
        for phrase in phrases:
            index.setdefault(phrase, section)

    for section, phrases in get_vocabulary().headings:
        for phrase in phrases:
            index.setdefault(phrase, section)

    return index


@lru_cache(maxsize=1)
def _fillers() -> frozenset:
    from app.extraction.rules.vocabulary import get_vocabulary

    return FILLER_WORDS | get_vocabulary().filler_words


def clear_cache() -> None:
    _phrase_index.cache_clear()
    _fillers.cache_clear()


def _segment(words: List[str]) -> Optional[List[str]]:
    """Splits words into known phrases; returns the sections of the phrases."""

    index = _phrase_index()

    if not words:
        return []

    for size in range(min(MAX_PHRASE_WORDS, len(words)), 0, -1):
        phrase = " ".join(words[:size])

        if phrase in index:
            rest = _segment(words[size:])

            if rest is not None:
                return [index[phrase], *rest]

    return None


def heading_section(line: str) -> Optional[str]:
    """
    Returns the section a heading line introduces, or None if the line is
    not a heading. For "Skills and Certifications" the first section wins.
    """

    stripped = line.strip()

    if not stripped or len(stripped) > MAX_HEADING_CHARS:
        return None

    if stripped.endswith((".", ",", ";")):
        return None

    stripped = _NUMBERING.sub("", stripped)

    words = normalise(stripped).split()

    if not words or len(words) > MAX_HEADING_WORDS:
        return None

    if any(char.isdigit() for char in stripped):
        return None

    # A phrase may contain a filler word ("additional information"), so the
    # words are tried as written before the fillers are dropped.
    fillers = _fillers()
    core = [word for word in words if word not in fillers]

    sections = _segment(words) or _segment(core)

    if not sections:
        return None

    return sections[0]


def split_by_headings(text: str) -> List[Tuple[Optional[str], str]]:
    """
    Splits text at heading lines.

    Returns (section, body) pairs in order. The first pair has section None
    when there is text before the first heading. Heading lines are removed
    from the bodies; pairs with an empty body are dropped.
    """

    segments: List[Tuple[Optional[str], List[str]]] = [(None, [])]

    for line in text.splitlines():
        section = heading_section(line)

        if section is not None:
            segments.append((section, []))
        elif line.strip():
            segments[-1][1].append(line)

    return [
        (section, "\n".join(body))
        for section, body in segments
        if body
    ]


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# A phone number starts with +, a leading 0 or an opening parenthesis; this
# keeps year ranges such as "2020 - 2023" from looking like one.
_PHONE = re.compile(r"(?<![\w.])(?:\+|0|\()[\d\s().-]{7,}\d")
_PROFILE = re.compile(r"(?:linkedin|github)\.com|www\.", re.IGNORECASE)


def looks_like_contact(text: str) -> bool:
    """True if the text contains an email address, phone number or profile link."""

    return bool(
        _EMAIL.search(text) or _PHONE.search(text) or _PROFILE.search(text)
    )


MAX_HEADER_LINES = 10
MAX_TRAILING_HEADER_LINES = 2
MAX_TRAILING_HEADER_WORDS = 5
NEWLINE = chr(10)


def split_contact_header(text: str) -> Tuple[str, str]:
    """
    Splits the CV header (name and contact lines) from the text after it.

    The header ends at the last line, within the first MAX_HEADER_LINES
    lines, that contains an email address, phone number or profile link.
    Returns (header, rest); the header is empty when no such line exists.
    """

    lines = [line for line in text.splitlines() if line.strip()]

    last_contact = -1

    for index, line in enumerate(lines[:MAX_HEADER_LINES]):
        if looks_like_contact(line):
            last_contact = index

    if last_contact < 0:
        return "", NEWLINE.join(lines)

    end = last_contact + 1

    # A location or title line often follows the contact lines.
    while (
        end < len(lines)
        and end - last_contact <= MAX_TRAILING_HEADER_LINES
        and _is_short_plain_line(lines[end])
    ):
        end += 1

    return (
        NEWLINE.join(lines[:end]),
        NEWLINE.join(lines[end:]),
    )


def _is_short_plain_line(line: str) -> bool:
    return (
        len(line.split()) <= MAX_TRAILING_HEADER_WORDS
        and not any(char.isdigit() for char in line)
        and heading_section(line) is None
    )
