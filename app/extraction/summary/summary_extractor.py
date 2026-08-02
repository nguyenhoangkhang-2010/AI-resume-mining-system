import re


class SummaryExtractor:

    SECTION_HEADERS = [
        "summary",
        "profile",
        "professional summary",
        "career summary",
        "objective",
        "about me",
        "overview",
    ]


    @staticmethod
    def extract(
        text: str
    ) -> str | None:

        if not text:
            return None

        normalized = text.replace(
            "\r\n",
            "\n"
        )

        pattern = (
            r"("
            + "|".join(
                SummaryExtractor.SECTION_HEADERS
            )
            + r")"
            r"\s*[:\-]?\s*\n"
            r"(.*?)(?=\n[A-Z][A-Z\s]{2,}\n|$)"
        )

        match = re.search(
            pattern,
            normalized,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        summary = match.group(2).strip()

        if not summary:
            return None

        return summary