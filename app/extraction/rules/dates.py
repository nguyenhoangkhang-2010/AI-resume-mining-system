"""
Date ranges as they are written in CVs.

Month names, the words for "until now" and the words that join the two ends of
a range come from the vocabulary files, so a new language needs data only. The
number formats are the same everywhere: 2021, 03/2021, 03.2021, 2021.03,
Mar 2021, Tháng 3/2021.
"""

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Pattern, Tuple

from app.extraction.rules.vocabulary import Vocabulary, get_vocabulary

_YEAR = r"(?:19|20)\d{2}"
_DASHES = r"-|–|—|‑|~"

# What is left of a line after its date range is removed.
_LEFTOVER_EDGES = " \t|,;:-–—/·•."


def _strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")

    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(char)
    )


def _alternatives(entries: Tuple[str, ...]) -> str:
    """A regex alternation of the entries, with and without accents, longest first."""

    variants = {
        variant
        for entry in entries
        for variant in (entry, _strip_accents(entry))
    }

    return "|".join(
        re.escape(variant).replace(r"\ ", r"\s+")
        for variant in sorted(variants, key=len, reverse=True)
    )


@dataclass(frozen=True)
class _Patterns:
    range: Pattern[str]
    present: Pattern[str]


@lru_cache(maxsize=4)
def _compile(vocabulary: Vocabulary) -> _Patterns:
    months = _alternatives(vocabulary.months) or r"(?!x)x"
    present = _alternatives(vocabulary.present) or r"(?!x)x"
    joiners = _alternatives(vocabulary.range_words)
    dash = rf"\s*(?:{_DASHES}{'|' + joiners if joiners else ''})\s*"

    point = (
        # 03/2021  03.2021  Tháng 3/2021  (month name optional before the number)
        rf"(?:(?:(?:{months})\.?\s*)?\d{{1,2}}\s*[/.\-]\s*{_YEAR}"
        # 2021.03  2021/03
        rf"|{_YEAR}\s*[/.]\s*\d{{1,2}}(?!\d)"
        # Mar 2021  March, 2021
        rf"|(?:{months})\.?,?\s*{_YEAR}"
        # 2021
        rf"|{_YEAR})"
    )

    until_now = rf"(?:{present})\.?"

    return _Patterns(
        range=re.compile(
            rf"(?P<start>{point}){dash}(?P<end>{point}|{until_now})(?!\w)",
            re.IGNORECASE,
        ),
        present=re.compile(rf"(?:{present})\.?", re.IGNORECASE),
    )


@dataclass(frozen=True)
class DateRange:
    start: str
    end: str
    # The line with the range removed ("Backend Engineer |" -> "Backend Engineer")
    rest: str
    # How much of the line the range took up (1.0 = the whole line)
    share: float


def _balanced(text: str) -> str:
    """Drops a bracket left over from removing the date inside it: "(2020 - 2021)"."""

    for opening, closing in (("(", ")"), ("[", "]")):
        if text.startswith(opening) and closing not in text:
            text = text[1:]

        if text.endswith(closing) and opening not in text:
            text = text[:-1]

    return text.strip(_LEFTOVER_EDGES)


def find_range(line: str) -> Optional[DateRange]:
    match = _compile(get_vocabulary()).range.search(line)

    if match is None:
        return None

    rest = (line[: match.start()] + " " + line[match.end():]).strip(_LEFTOVER_EDGES)
    rest = re.sub(r"[(\[]\s*[)\]]", " ", rest)
    rest = _balanced(" ".join(rest.split()))

    return DateRange(
        start=match.group("start").strip(),
        end=match.group("end").strip(),
        rest=rest,
        share=(match.end() - match.start()) / max(1, len(line.strip())),
    )


def year_of(text: str) -> Optional[int]:
    """The last four-digit year in the text, if any."""

    years: List[str] = re.findall(rf"\b{_YEAR}\b", text)

    return int(years[-1]) if years else None


def is_present(text: str) -> bool:
    return _compile(get_vocabulary()).present.fullmatch(text.strip()) is not None
