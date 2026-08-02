import re

from typing import Dict


class ContactExtractor:

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+"
        r"@[a-zA-Z0-9.-]+"
        r"\.[a-zA-Z]{2,}"
    )

    PHONE_PATTERN = re.compile(
        r"(\+?\d[\d\s().-]{8,}\d)"
    )

    LINKEDIN_PATTERN = re.compile(
        r"(https?://)?"
        r"(www\.)?"
        r"linkedin\.com/in/[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )

    GITHUB_PATTERN = re.compile(
        r"(https?://)?"
        r"(www\.)?"
        r"github\.com/[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )


    @staticmethod
    def extract(
        text: str
    ) -> Dict[str, str | None]:

        return {
            "email": ContactExtractor._extract_first(
                ContactExtractor.EMAIL_PATTERN,
                text
            ),

            "phone": ContactExtractor._extract_first(
                ContactExtractor.PHONE_PATTERN,
                text
            ),

            "linkedin": ContactExtractor._extract_first(
                ContactExtractor.LINKEDIN_PATTERN,
                text
            ),

            "github": ContactExtractor._extract_first(
                ContactExtractor.GITHUB_PATTERN,
                text
            ),
        }

    @staticmethod
    def _extract_first(
        pattern,
        text: str
    ):

        match = pattern.search(text)

        if match:
            return match.group(0)

        return None