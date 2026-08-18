from __future__ import annotations

import json
from typing import Any, Dict, List

from loguru import logger

from app.extraction.llm.llm_extractor import LLMExtractor


class EducationExtractor:

    EXTRACTION_PROMPT = """
    You are a structured resume information extraction system.

    Extract ONLY education entries from the provided resume text.

    The input may contain:
    - multiple languages
    - different resume layouts
    - different institution naming conventions
    - different degree descriptions
    - different date formats
    - GPA or equivalent academic scores
    - additional academic information

    Use semantic understanding rather than fixed keywords, institution names,
    degree names, university names, country names, or resume templates.

    Return ONLY valid JSON.
    Do not include markdown.
    Do not include explanations.

    Required output:

    {
    "education": [
        {
        "institution": null,
        "degree_level": [],
        "start_year": null,
        "end_year": null,
        "gpa": null
        }
    ]
    }

    Extraction rules:

    - institution:
    Extract the educational institution associated with the entry.
    Preserve the source wording whenever possible.

    - degree_level:
    Extract the semantic level/type of degree or academic program.
    Normalize equivalent descriptions only when their meaning is clear.
    Do not infer a degree that is not supported by the source.

    - start_year:
    Extract the starting year of the education period when explicitly
    available.

    - end_year:
    Extract the ending year when explicitly available.
    If the education is ongoing, return null.

    - gpa:
    Extract only an overall GPA or clearly equivalent overall academic score.
    Do not use individual course grades as GPA.

    - Multiple education entries must produce multiple objects.

    - Do not fabricate missing values.

    - If a field cannot be confidently determined, return null or [].

    Important:
    Only extract information supported by the provided text.
    Do not use outside knowledge.
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

        if not isinstance(text, str):
            return []

        text = text.strip()

        if not text:
            return []

        logger.debug(
            "Starting semantic education extraction | input_chars={}",
            len(text),
        )

        raw_result = self.llm_extractor.extract_info(
            text=text,
            prompt_template=self.EXTRACTION_PROMPT,
            max_new_tokens=192,
        )

        if not raw_result:
            logger.warning(
                "Education LLM extraction returned empty output."
            )
            return []

        result = self._parse_result(
            raw_result
        )

        logger.debug(
            "Education extraction completed | entries={}",
            len(result),
        )

        return result

    @classmethod
    def _parse_result(
        cls,
        raw_result: str,
    ) -> List[Dict[str, Any]]:

        if not isinstance(raw_result, str):
            return []

        text = cls._clean_json_response(
            raw_result
        )

        if not text:
            return []

        try:
            parsed = json.loads(text)

        except json.JSONDecodeError as exc:
            logger.warning(
                "Failed to parse education LLM output as JSON: {}",
                exc,
            )
            return []

        if not isinstance(parsed, dict):
            return []

        education = parsed.get(
            "education"
        )

        if not isinstance(education, list):
            return []

        normalized: List[Dict[str, Any]] = []

        for item in education:

            if not isinstance(item, dict):
                continue

            entry = {
                "institution": cls._normalize_string(
                    item.get("institution")
                ),
                "degree_level": cls._normalize_degree_level(
                    item.get("degree_level")
                ),
                "start_year": cls._normalize_year(
                    item.get("start_year")
                ),
                "end_year": cls._normalize_year(
                    item.get("end_year")
                ),
                "gpa": cls._normalize_gpa(
                    item.get("gpa")
                ),
            }

            if cls._is_empty_entry(entry):
                continue

            normalized.append(entry)

        return normalized

    @staticmethod
    def _clean_json_response(
        raw_result: str,
    ) -> str:

        text = raw_result.strip()

        if not text:
            return ""

        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        if not text.startswith("{"):

            start = text.find("{")

            if start >= 0:
                text = text[start:]

        if not text.endswith("}"):

            end = text.rfind("}")

            if end >= 0:
                text = text[: end + 1]

        return text.strip()

    @staticmethod
    def _is_empty_entry(
        entry: Dict[str, Any],
    ) -> bool:

        return not any(
            (
                entry["institution"],
                entry["degree_level"],
                entry["start_year"] is not None,
                entry["end_year"] is not None,
                entry["gpa"] is not None,
            )
        )

    @staticmethod
    def _normalize_string(
        value: Any,
    ) -> str | None:

        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _normalize_degree_level(
        value: Any,
    ) -> List[str]:

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
    def _normalize_year(
        value: Any,
    ) -> int | None:

        if value is None or isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value) if value.is_integer() else None

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return None

            import re

            years = re.findall(
                r"\b(?:19|20)\d{2}\b",
                value,
            )

            if not years:
                return None

            return int(years[-1])

        return None

    @staticmethod
    def _normalize_gpa(
        value: Any,
    ) -> float | None:

        if value is None or isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, list):

            for item in value:

                result = EducationExtractor._normalize_gpa(
                    item
                )

                if result is not None:
                    return result

            return None

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return None

            import re

            match = re.search(
                r"\b(\d+(?:\.\d+)?)\s*/\s*(?:4|5|10)\b",
                value,
            )

            if match:
                return float(match.group(1))

            # Otherwise accept a plain numeric value.
            match = re.search(
                r"\b\d+(?:\.\d+)?\b",
                value,
            )

            if match:
                return float(match.group())

            return None

        return None