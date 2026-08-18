import re
from typing import Optional


class SocialDetector:

    LINKEDIN_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/"
        r"[A-Za-z0-9][A-Za-z0-9._-]*",
        re.IGNORECASE,
    )

    GITHUB_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?github\.com/"
        r"[A-Za-z0-9][A-Za-z0-9._-]*",
        re.IGNORECASE,
    )

    def detect_linkedin(self, text: str) -> Optional[str]:
        if not text:
            return None

        normalized_text = self._clean_text(text)

        match = self.LINKEDIN_PATTERN.search(normalized_text)

        if not match:
            return None

        return self._normalize_url(match.group(0))

    def detect_github(self, text: str) -> Optional[str]:
        if not text:
            return None

        normalized_text = self._clean_text(text)

        match = self.GITHUB_PATTERN.search(normalized_text)

        if not match:
            return None

        return self._normalize_url(match.group(0))

    @staticmethod
    def _clean_text(text: str) -> str:

        if not text:
            return ""

        text = re.sub(
            r"\[([^\]]+)\]\(([^)]*)\)",
            r"\1 \2",
            text,
        )

        text = text.replace(r"\:", ":")
        text = text.replace(r"\.", ".")
        text = text.replace(r"\/", "/")

        return text

    @staticmethod
    def _normalize_url(url: str) -> str:
        url = url.strip()

        url = url.replace("\\", "")

        if not url.lower().startswith(
            ("http://", "https://")
        ):
            url = "https://" + url

        return url.rstrip("/")