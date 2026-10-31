from __future__ import annotations

import json
from typing import Any, Dict, List

from loguru import logger

from app.core.config.settings import settings
from app.extraction.grounding import ground_entries
from app.extraction.rules import stats
from app.extraction.rules.experience_rules import parse_experience
from app.extraction.llm.json_recovery import recover_array_objects
from app.extraction.llm.llm_extractor import LLMExtractor


class ExperienceExtractor:

    EXTRACTION_PROMPT = """
    You are a multilingual resume information extraction system.

    Extract professional experience from the input text.

    Infer the semantic structure from the source text.
    Do not rely on fixed company names, job titles, industries, keywords,
    templates, languages, or date formats.

    Return ONLY valid JSON with this structure:

    {
    "experience": [
        {
        "company": null,
        "role": null,
        "start_date": null,
        "end_date": null,
        "description": [],
        "employment_type": null,
        "location": null,
        "achievements": []
        }
    ]
    }

    Rules:

    - company: organization or entity associated with the experience.
    - role: person's position, role, or function.
    - start_date/end_date: preserve the source representation.
    - description: responsibilities, activities, duties, and contributions.
    - employment_type: infer only when clearly supported by the text.
    - location: associated location when available.
    - achievements: explicit results, measurable outcomes, awards,
    improvements, or accomplishments only.
    - Preserve source meaning and wording.
    - Keep separate experiences separate.
    - Do not fabricate missing information.
    - Use null for unknown scalar fields and [] for unknown list fields.
    - Interpret multilingual content semantically.
    - Return ONLY the JSON object.
"""

    def __init__(
        self,
        llm_extractor: LLMExtractor,
    ) -> None:
        self.llm_extractor = llm_extractor

    def extract(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:

        if not text or not text.strip():
            return []

        # Regular layouts are read directly; only the rest needs the model.
        if settings.EXTRACTION_RULES_FIRST:
            by_rules = parse_experience(text)

            stats.record("experience", by_rules is not None)

            if by_rules is not None:
                logger.debug(
                    "Experience read by rules: {} entries.",
                    len(by_rules),
                )

                return by_rules

        logger.debug(
            "Starting semantic experience extraction."
        )

        raw_result = self.llm_extractor.extract_info(
            text=text,
            prompt_template=self.EXTRACTION_PROMPT,
            max_new_tokens=settings.LLM_EXPERIENCE_MAX_TOKENS,
        )

        if not raw_result:
            logger.warning(
                "Experience LLM extraction returned empty output."
            )
            return []

        result = ground_entries(
            self._parse_result(raw_result),
            ("company", "role", "location"),
            text,
            "experience",
        )

        logger.debug(
            "Extracted {} experience records.",
            len(result),
        )

        return result

    @classmethod
    def _parse_result(
        cls,
        raw_result: str,
    ) -> List[Dict[str, Any]]:

        if not raw_result:
            return []

        text = cls._remove_markdown_code_fence(
            raw_result.strip()
        )

        parsed = cls._parse_json(
            text
        )

        if parsed is None:
            logger.warning(
                "Failed to parse experience LLM output as JSON."
            )
            return []

        if isinstance(parsed, list):
            experiences = parsed

        elif isinstance(parsed, dict):
            experiences = parsed.get(
                "experience",
                [],
            )

        else:
            return []

        if not isinstance(experiences, list):
            return []

        normalized: List[Dict[str, Any]] = []

        for item in experiences:

            if not isinstance(item, dict):
                continue

            entry = {
                "company": cls._normalize_string(
                    item.get("company")
                ),
                "role": cls._normalize_string(
                    item.get("role")
                ),
                "start_date": cls._normalize_string(
                    item.get("start_date")
                ),
                "end_date": cls._normalize_string(
                    item.get("end_date")
                ),
                "description": cls._normalize_string_list(
                    item.get("description")
                ),
                "employment_type": cls._normalize_string(
                    item.get("employment_type")
                ),
                "location": cls._normalize_string(
                    item.get("location")
                ),
                "achievements": cls._normalize_string_list(
                    item.get("achievements")
                ),
            }

            if not cls._has_content(entry):
                continue

            normalized.append(entry)

        return normalized

    @staticmethod
    def _remove_markdown_code_fence(
        text: str,
    ) -> str:

        if not text.startswith("```"):
            return text

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        return "\n".join(lines).strip()

    @staticmethod
    def _parse_json(
        text: str,
    ) -> Any | None:

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")

        if start >= 0 and end > start:

            candidate = text[
                start:end + 1
            ]

            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        start = text.find("[")
        end = text.rfind("]")

        if start >= 0 and end > start:

            candidate = text[
                start:end + 1
            ]

            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # The model stops at its token limit in the middle of the list:
        # keep the entries that were completed instead of losing them all.
        recovered = recover_array_objects(text, "experience")

        if recovered:
            logger.warning(
                "LLM output appears truncated. Recovered {} complete "
                "experience entr{}.",
                len(recovered),
                "y" if len(recovered) == 1 else "ies",
            )
            return recovered

        return None

    @staticmethod
    def _normalize_string(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _normalize_string_list(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(value, str):

            value = value.strip()

            return [value] if value else []

        if not isinstance(value, list):
            return []

        result: List[str] = []

        for item in value:

            if not isinstance(item, str):
                continue

            item = item.strip()

            if item:
                result.append(item)

        return result

    @staticmethod
    def _has_content(
        entry: Dict[str, Any],
    ) -> bool:

        return any(
            bool(value)
            for value in entry.values()
        )