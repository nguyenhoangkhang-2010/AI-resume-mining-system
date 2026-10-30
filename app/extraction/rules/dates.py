"""Date ranges as they are written in CVs, in English and Vietnamese."""

import re
from dataclasses import dataclass
from typing import Optional

_MONTHS = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)

# 2021 | 03/2021 | 03.2021 | 03-2021 | Mar 2021 | March, 2021 | Tháng 3/2021
_POINT = (
    rf"(?:(?:th[áa]ng\s*)?\d{{1,2}}\s*[/.\-]\s*(?:19|20)\d{{2}}"
    rf"|(?:{_MONTHS})\.?,?\s*(?:19|20)\d{{2}}"
    rf"|(?:19|20)\d{{2}})"
)

_PRESENT = (
    r"present|current|currently|now|today|ongoing|to date|"
    r"nay|hi[ệe]n\s*t[ạa]i|hi[ệe]n\s*nay|đ[ếe]n\s*nay"
)

_DASH = r"\s*(?:-|–|—|‑|~|to|until|till|đến|den)\s*"

RANGE = re.compile(
    rf"(?P<start>{_POINT}){_DASH}(?P<end>{_POINT}|{_PRESENT})",
    re.IGNORECASE,
)

# What is left of a line after its date range is removed.
_LEFTOVER_EDGES = " \t|,;:-–—()[]/·•"


@dataclass(frozen=True)
class DateRange:
    start: str
    end: str
    # The line with the range removed ("Backend Engineer |" -> "Backend Engineer")
    rest: str
    # How much of the line the range took up (1.0 = the whole line)
    share: float


def find_range(line: str) -> Optional[DateRange]:
    match = RANGE.search(line)

    if match is None:
        return None

    rest = (line[: match.start()] + " " + line[match.end():]).strip(_LEFTOVER_EDGES)
    rest = " ".join(rest.split())

    return DateRange(
        start=match.group("start").strip(),
        end=match.group("end").strip(),
        rest=rest,
        share=(match.end() - match.start()) / max(1, len(line.strip())),
    )


def year_of(text: str) -> Optional[int]:
    """The last four-digit year in the text, if any."""

    years = re.findall(r"\b(?:19|20)\d{2}\b", text)

    return int(years[-1]) if years else None


def is_present(text: str) -> bool:
    return re.fullmatch(_PRESENT, text.strip(), re.IGNORECASE) is not None
