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


    def extract(
        self,
        text: str
    ) -> Dict[str, str | None]:

        return {
            "email": self._extract_first(
                self.EMAIL_PATTERN,
                text
            ),

            "phone": self._extract_first(
                self.PHONE_PATTERN,
                text
            ),

            "linkedin": self._extract_first(
                self.LINKEDIN_PATTERN,
                text
            ),

            "github": self._extract_first(
                self.GITHUB_PATTERN,
                text
            ),
        }


    def _extract_first(
        self,
        pattern,
        text: str
    ):

        match = pattern.search(text)

        if match:
            return match.group(0)

        return None