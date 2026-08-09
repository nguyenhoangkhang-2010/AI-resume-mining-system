import re
from typing import Optional

from .name_detector import NameDetector
from .email_extractor import EmailExtractor
from .social_detector import SocialDetector
from app.extraction.ner.ner_service import NERService


class PersonalExtractor:

    PHONE_PATTERN = re.compile(
        r"\+?\d[\d\s().-]{8,}\d"
    )

    def __init__(self):
        self.name_detector = NameDetector()
        self.email_extractor = EmailExtractor()
        self.social_detector = SocialDetector()
        self.ner_service = NERService()

    def extract(self, text: str) -> dict:

        if not text:
            return self._empty_result()

        normalized_text = self._normalize_text(text)

        full_name = self.name_detector.detect(
            normalized_text
        )

        if not full_name:
            full_name = self._extract_name_with_ner(
                normalized_text
            )

        return {
            "full_name": full_name,
            "email": self.email_extractor.extract(
                normalized_text
            ),
            "phone": self.extract_phone(
                normalized_text
            ),
            "linkedin": self.social_detector.detect_linkedin(
                normalized_text
            ),
            "github": self.social_detector.detect_github(
                normalized_text
            ),
        }

    def _extract_name_with_ner(
        self,
        text: str,
    ) -> Optional[str]:

        entities = self.ner_service.extract(text)

        for entity in entities:
            if entity.get("label") == "PERSON":
                value = entity.get("text")

                if value:
                    return value.strip()

        return None

    def extract_phone(
        self,
        text: str,
    ) -> Optional[str]:

        if not text:
            return None

        match = self.PHONE_PATTERN.search(text)

        if not match:
            return None

        return match.group(0).strip()

    def _normalize_text(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        text = text.replace(
            r"\:",
            ":",
        )

        text = text.replace(
            r"\@",
            "@",
        )

        text = re.sub(
            r"\[([^\]]+)\]\(([^)]*)\)",
            r"\1",
            text,
        )

        text = re.sub(
            r"mailto:",
            "",
            text,
            flags=re.IGNORECASE,
        )

        return text

    @staticmethod
    def _empty_result() -> dict:

        return {
            "full_name": None,
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
        }