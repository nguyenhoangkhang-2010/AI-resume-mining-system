import re


class ExperienceYearsExtractor:
    """
    Extracts the minimum years of experience a job asks for,
    e.g. "3+ years", "2-4 years", "5 yrs".
    """

    MAX_YEARS = 40

    YEARS_PATTERN = re.compile(
        r"(?P<low>\d{1,2})"
        r"\s*(?:\+|plus)?"
        r"(?:\s*(?:-|–|to)\s*(?P<high>\d{1,2}))?"
        r"\s*\+?\s*"
        r"(?:years?|yrs?)\b"
        r"(?!\s*old)",
        re.IGNORECASE,
    )

    @classmethod
    def extract(
        cls,
        text: str,
    ) -> int | None:

        if not text:
            return None

        lower_bounds = [
            int(match.group("low"))
            for match in cls.YEARS_PATTERN.finditer(text)
        ]

        lower_bounds = [
            years
            for years in lower_bounds
            if 0 < years <= cls.MAX_YEARS
        ]

        if not lower_bounds:
            return None

        return max(lower_bounds)
