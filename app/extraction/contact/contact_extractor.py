import re
from typing import Dict, Optional, Pattern


class ContactExtractor:
    """
    Extract contact information from resume text.

    Supports:
    - plain email
    - Markdown email links
    - plain phone numbers
    - plain LinkedIn URLs
    - Markdown LinkedIn links
    - plain GitHub URLs
    - Markdown GitHub links
    """

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}"
    )

    PHONE_PATTERN = re.compile(
        r"\+?\d[\d\s().-]{8,}\d"
    )

    LINKEDIN_PATTERN = re.compile(
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"linkedin\.com/in/[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )

    GITHUB_PATTERN = re.compile(
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"github\.com/[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )

    MARKDOWN_LINK_PATTERN = re.compile(
        r"\[([^\]]*)\]\(([^)]*)\)"
    )

    MAILTO_PATTERN = re.compile(
        r"^mailto:",
        re.IGNORECASE,
    )

    PATTERNS: Dict[str, Pattern[str]] = {
        "email": EMAIL_PATTERN,
        "phone": PHONE_PATTERN,
        "linkedin": LINKEDIN_PATTERN,
        "github": GITHUB_PATTERN,
    }

    def extract(
        self,
        text: str,
    ) -> Dict[str, str]:

        if not text:
            return {}

        normalized_text = self._normalize_text(text)

        result: Dict[str, str] = {}

        for field_name, pattern in self.PATTERNS.items():

            value = self._extract_first(
                pattern,
                normalized_text,
            )

            if value:
                result[field_name] = value

        return result

    @classmethod
    def _normalize_text(
        cls,
        text: str,
    ) -> str:

        if not text:
            return ""

        def replace_markdown_link(
            match: re.Match[str],
        ) -> str:

            label = match.group(1).strip()
            target = match.group(2).strip()

            # Remove accidental backslash escaping.
            target = target.replace(r"\:", ":")
            target = target.replace(r"\@", "@")

            # mailto: URL
            if cls.MAILTO_PATTERN.match(target):

                email = cls.MAILTO_PATTERN.sub(
                    "",
                    target,
                ).strip()

                email_match = cls.EMAIL_PATTERN.search(
                    email
                )

                if email_match:
                    return email_match.group(0)

                return label

            # HTTP/HTTPS URL
            if re.match(
                r"^https?://",
                target,
                re.IGNORECASE,
            ):
                return target

            # Unknown Markdown link:
            # keep the visible label.
            return label

        normalized = cls.MARKDOWN_LINK_PATTERN.sub(
            replace_markdown_link,
            text,
        )

        return normalized

    @staticmethod
    def _extract_first(
        pattern: Pattern[str],
        text: str,
    ) -> Optional[str]:

        match = pattern.search(text)

        if not match:
            return None

        return match.group(0).strip()