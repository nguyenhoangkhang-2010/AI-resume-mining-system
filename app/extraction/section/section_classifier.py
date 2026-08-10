from __future__ import annotations

from typing import Optional

from loguru import logger

from app.extraction.llm.llm_extractor import LLMExtractor


class SectionClassifier:

    CANONICAL_SECTIONS = (
        "personal_info",
        "summary",
        "education",
        "experience",
        "skills",
        "projects",
        "certifications",
        "awards",
        "activities",
        "languages",
        "publications",
        "references",
        "interests",
        "additional_information",
        "unknown",
    )

    def __init__(
        self,
        llm_extractor: Optional[LLMExtractor] = None,
    ) -> None:

        self.llm_extractor = (
            llm_extractor
            if llm_extractor is not None
            else LLMExtractor()
        )

    def classify(self, heading: str) -> str:

        if not heading or not heading.strip():
            return "unknown"

        heading = heading.strip()

        prompt = self._build_prompt(heading)

        try:
            response = self.llm_extractor.extract_info(
                heading,
                prompt,
            )

            logger.info(
                "Raw LLM response for '{}': {!r}",
                heading,
                response,
            )

            section = self._parse_response(response)

            if section:
                logger.debug(
                    "Section classified: '{}' -> '{}'",
                    heading,
                    section,
                )

                return section

        except Exception as exc:
            logger.warning(
                "LLM section classification failed for '{}': {}",
                heading,
                exc,
            )

        return "unknown"

    @classmethod
    def _build_prompt(
        cls,
        heading: str,
    ) -> str:

        labels = "\n".join(
            f"- {label}"
            for label in cls.CANONICAL_SECTIONS
        )

        return f"""
You are a resume section classifier.

Your task is to understand the semantic meaning of
a resume section heading.

Map the heading to exactly ONE canonical section.

Allowed canonical sections:

{labels}

Rules:

1. Classify by semantic meaning, not exact wording.
2. The heading may use any language or wording.
3. Do not rely on predefined aliases.
4. Do not invent a new section.
5. Return ONLY one canonical section name.
6. If the meaning cannot be determined reliably,
   return "unknown".

Resume section heading:

{heading}
""".strip()

    @classmethod
    def _parse_response(
        cls,
        response: str,
    ) -> Optional[str]:

        if not response:
            return None

        value = response.strip().lower()

        value = value.strip("`'\" ")

        for label in sorted(
            cls.CANONICAL_SECTIONS,
            key=len,
            reverse=True,
        ):
            if value == label:
                return label

        return None