import re
from datetime import date
from typing import Any, Iterable, List, Optional, Tuple


class ExperienceCalculator:
    """
    Estimates a candidate's total years of work experience from the
    start/end dates of their experience entries.

    Dates are read at year granularity, overlapping jobs are counted
    once, and an entry without an end date is not counted beyond its
    start year (a conservative estimate).
    """

    YEAR_PATTERN = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")

    PRESENT_WORDS = (
        "present",
        "now",
        "current",
        "ongoing",
        "hiện tại",
        "nay",
    )

    def total_years(
        self,
        experiences: Iterable[Any],
        current_year: Optional[int] = None,
    ) -> float:

        current_year = current_year or date.today().year

        intervals: List[Tuple[int, int]] = []

        for experience in experiences or []:
            interval = self._interval(experience, current_year)

            if interval:
                intervals.append(interval)

        return float(self._union_length(intervals))

    def _interval(
        self,
        experience: Any,
        current_year: int,
    ) -> Optional[Tuple[int, int]]:

        start_text = self._field(experience, "start_date")
        end_text = self._field(experience, "end_date")

        start = self._first_year(start_text)

        if start is None or start > current_year:
            return None

        if end_text and any(
            word in end_text.casefold()
            for word in self.PRESENT_WORDS
        ):
            end = current_year
        else:
            end = self._first_year(end_text)

            if end is None:
                end = start

        end = min(end, current_year)

        if end < start:
            return None

        return start, end

    @staticmethod
    def _field(experience: Any, name: str) -> str:
        if isinstance(experience, dict):
            value = experience.get(name)
        else:
            value = getattr(experience, name, None)

        return value if isinstance(value, str) else ""

    def _first_year(self, text: str) -> Optional[int]:
        match = self.YEAR_PATTERN.search(text or "")

        return int(match.group(1)) if match else None

    @staticmethod
    def _union_length(
        intervals: List[Tuple[int, int]],
    ) -> int:

        total = 0
        current_start = current_end = None

        for start, end in sorted(intervals):
            if current_end is None or start > current_end:
                if current_end is not None:
                    total += current_end - current_start

                current_start, current_end = start, end
            else:
                current_end = max(current_end, end)

        if current_end is not None:
            total += current_end - current_start

        return total


class ExperienceScorer:
    """
    Scores a candidate's experience against the years a job asks
    for (0-100). Returns None when the job states no requirement.
    """

    def score(
        self,
        required_years: Optional[int],
        candidate_years: float,
    ) -> Optional[float]:

        if not required_years or required_years <= 0:
            return None

        ratio = min(candidate_years / required_years, 1.0)

        return round(ratio * 100, 2)
