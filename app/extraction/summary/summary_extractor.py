from __future__ import annotations

from loguru import logger

from app.extraction.llm.llm_extractor import LLMExtractor


class SummaryExtractor:

    EXTRACTION_PROMPT = """
    You are a multilingual resume information extraction system.

    Extract the professional summary, profile, career objective,
    personal professional introduction, or equivalent introductory
    statement from the provided resume text.

    The input may contain:

    - different languages
    - different resume formats
    - different section names
    - different ordering
    - different writing styles
    - missing explicit section headings

    Identify the semantic introductory content from the actual text.

    Do NOT rely on:

    - hard-coded section names
    - fixed keywords
    - fixed resume templates
    - fixed job titles
    - fixed industries
    - fixed organizations
    - fixed phrases

    Return ONLY valid JSON.

    Expected structure:

    {
        "summary": null
    }

    Rules:

    1. "summary":
    Return the original professional summary/objective/profile text
    when such content exists.

    2. Preserve the original wording as much as possible.

    3. Do not rewrite, summarize, translate, or improve the candidate's text.

    4. Do not combine unrelated sections into the summary.

    5. Do not include:
    - education
    - work experience
    - projects
    - certifications
    - skills
    - awards
    - personal contact information

    6. If the resume contains a career objective instead of a professional
    summary, return that objective as "summary".

    7. If multiple introductory paragraphs clearly belong to the same
    semantic summary/profile/objective section, preserve them together.

    8. If no professional summary, profile, objective, or equivalent
    introductory statement exists, return null.

    9. The input may be multilingual.

    10. Do not fabricate information.

    Return only the JSON object.
"""

    def __init__(
        self,
        llm_extractor: LLMExtractor,
    ) -> None:
        self.llm_extractor = llm_extractor

    def extract(
        self,
        text: str,
    ) -> str | None:

        if not text or not text.strip():
            return None

        logger.debug(
            "Starting semantic summary extraction."
        )

        raw_result = self.llm_extractor.extract_info(
            text=text,
            prompt_template=self.EXTRACTION_PROMPT,
        )

        if not raw_result:
            logger.warning(
                "Summary LLM extraction returned empty output."
            )
            return None

        summary = self._parse_result(
            raw_result
        )

        if summary is None:
            logger.debug(
                "No professional summary found."
            )
            return None

        logger.debug(
            "Summary extracted successfully."
        )

        return summary

    @staticmethod
    def _parse_result(
        raw_result: str,
    ) -> str | None:

        if not raw_result:
            return None

        text = raw_result.strip()

        text = SummaryExtractor._remove_code_fence(
            text
        )

        parsed = SummaryExtractor._parse_json(
            text
        )

        if not isinstance(
            parsed,
            dict,
        ):
            return None

        value = parsed.get(
            "summary"
        )

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return None

        value = value.strip()

        if not value:
            return None

        return value

    @staticmethod
    def _remove_code_fence(
        text: str,
    ) -> str:

        if not text.startswith("```"):
            return text

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        return "\n".join(
            lines
        ).strip()

    @staticmethod
    def _parse_json(
        text: str,
    ) -> dict | None:

        import json

        try:
            parsed = json.loads(
                text
            )

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

        except json.JSONDecodeError:
            pass

        # Recover JSON object if the LLM
        # adds surrounding text.
        start = text.find("{")
        end = text.rfind("}")

        if (
            start >= 0
            and end > start
        ):
            candidate = text[
                start:end + 1
            ]

            try:
                parsed = json.loads(
                    candidate
                )

                if isinstance(
                    parsed,
                    dict,
                ):
                    return parsed

            except json.JSONDecodeError:
                pass

        return None