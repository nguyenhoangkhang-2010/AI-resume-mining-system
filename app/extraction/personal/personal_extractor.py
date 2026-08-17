from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.extraction.ner.ner_service import NERService

from .email_extractor import EmailExtractor
from .name_detector import NameDetector
from .social_detector import SocialDetector


class PersonalExtractor:

    PHONE_PATTERN = re.compile(
        r"""
        (?<!\w)
        (?:
            \+\d{1,3}
            |
            \(\+\d{1,3}\)
            |
            0
        )
        [\s().-]*
        \d
        (?:[\d\s().-]{6,}\d)?
        (?!\w)
        """,
        re.VERBOSE,
    )

    def __init__(
        self,
        ner_service: NERService,
    ) -> None:

        self.ner_service = ner_service

        self.name_detector = NameDetector(
            ner_service=self.ner_service,
        )

        self.email_extractor = EmailExtractor()
        self.social_detector = SocialDetector()

    def extract(
        self,
        text: str,
    ) -> Dict[str, Optional[str]]:

        if not text or not text.strip():
            return self._empty_result()

        normalized_text = self._normalize_text(
            text
        )

        full_name = self._extract_name(
            normalized_text
        )

        email = self.email_extractor.extract(
            normalized_text
        )

        phone = self._extract_phone(
            normalized_text
        )

        linkedin = (
            self.social_detector.detect_linkedin(
                normalized_text
            )
        )

        github = (
            self.social_detector.detect_github(
                normalized_text
            )
        )

        return {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
        }

    def _extract_name(
        self,
        text: str,
    ) -> Optional[str]:

        name = self.name_detector.detect(
            text
        )

        if name:
            return name.strip()

        return self._extract_name_with_ner(
            text
        )

    def _extract_name_with_ner(
        self,
        text: str,
    ) -> Optional[str]:

        if not text:
            return None

        try:
            entities = self.ner_service.extract(
                text
            )
        except Exception:
            return None

        candidates = []

        for entity in entities:

            if not isinstance(
                entity,
                dict,
            ):
                continue

            label = str(
                entity.get(
                    "label",
                    "",
                )
            ).upper()

            if label not in {
                "PERSON",
                "PER",
                "NAME",
            }:
                continue

            value = entity.get(
                "text"
            )

            if not isinstance(
                value,
                str,
            ):
                continue

            value = value.strip()

            if not value:
                continue

            score = self._entity_score(
                entity
            )

            candidates.append(
                (
                    score,
                    value,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item[0],
                len(item[1]),
            ),
            reverse=True,
        )

        return candidates[0][1]

    @staticmethod
    def _entity_score(
        entity: Dict[str, Any],
    ) -> float:

        value = entity.get(
            "score",
            0.0,
        )

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _extract_phone(
        self,
        text: str,
    ) -> Optional[str]:

        if not text:
            return None

        matches = self.PHONE_PATTERN.findall(
            text
        )

        if not matches:
            return None

        candidates = []

        for value in matches:

            cleaned = self._clean_phone(
                value
            )

            if not cleaned:
                continue

            digits = re.sub(
                r"\D",
                "",
                cleaned,
            )

            if len(digits) < 8:
                continue

            if len(digits) > 15:
                continue

            if (
                len(digits) == 4
                and 1900 <= int(digits) <= 2100
            ):
                continue

            candidates.append(
                cleaned
            )

        if not candidates:
            return None

        return candidates[0]

    @staticmethod
    def _clean_phone(
        value: str,
    ) -> str:

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        value = value.strip(
            ".,;:"
        )

        return value

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        if not text:
            return ""

        normalized = text

        normalized = normalized.replace(
            r"\:",
            ":",
        )

        normalized = normalized.replace(
            r"\@",
            "@",
        )

        normalized = re.sub(
            r"\[([^\]]+)\]\(([^)]*)\)",
            r"\1",
            normalized,
        )

        normalized = re.sub(
            r"mailto:",
            "",
            normalized,
            flags=re.IGNORECASE,
        )

        return normalized

    @staticmethod
    def _empty_result() -> Dict[
        str,
        Optional[str],
    ]:

        return {
            "full_name": None,
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
        }