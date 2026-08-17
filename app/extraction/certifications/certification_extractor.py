from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from app.extraction.llm.llm_extractor import LLMExtractor


class CertificationExtractor:

    EXTRACTION_PROMPT = """
    You are a multilingual resume information extraction system.

    Extract formal certifications, certificates, licenses, credentials,
    and equivalent formally issued qualifications from the provided resume
    section.

    The input may contain:
    - different languages
    - different resume formats
    - different date formats
    - bullet lists
    - inline information
    - multiple certifications
    - issuer information
    - credential identifiers
    - verification URLs

    Infer the semantic structure from the actual text.

    Do NOT rely on:
    - hard-coded certification names
    - hard-coded issuer names
    - hard-coded organizations
    - hard-coded industries
    - fixed keywords
    - fixed resume templates
    - fixed section headers

    Do NOT classify the following as certifications unless the source
    explicitly identifies them as formal credentials:

    - university degrees
    - academic coursework
    - ordinary skills
    - projects
    - work experience
    - scholarships
    - honors
    - awards
    - achievements

    Return ONLY valid JSON.

    Expected structure:

    {
        "certifications": [
            {
                "name": null,
                "issuer": null,
                "issue_date": null,
                "expiry_date": null,
                "credential_id": null,
                "credential_url": null
            }
        ]
    }

    Rules:

    1. name:
    Extract the certification, certificate, license, or credential name.

    2. issuer:
    Extract the organization or authority that issued the credential
    when explicitly available.

    3. issue_date:
    Extract the issue date or issue year when available.

    4. expiry_date:
    Extract the expiration date when explicitly available.

    5. credential_id:
    Extract a credential ID, certificate number, license number,
    registration number, or equivalent identifier when available.

    6. credential_url:
    Extract a verification URL or credential URL when available.

    7. Preserve the original wording whenever possible.

    8. Do not fabricate missing information.

    9. If a field cannot be confidently extracted, return null.

    10. If multiple certifications exist, return multiple objects.

    11. Do not merge separate certifications into one object.

    12. Do not create a certification merely because a technology,
        skill, course, or organization name appears in the text.

    13. The input may contain multilingual content.
        Understand the semantic meaning regardless of language.

    14. Return an empty certifications list when no formal certification,
        certificate, license, or credential can be identified.

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
    ) -> List[Dict[str, Any]]:

        if not text or not text.strip():
            return []

        logger.debug(
            "Starting semantic certification extraction."
        )

        raw_result = self.llm_extractor.extract_info(
            text=text,
            prompt_template=self.EXTRACTION_PROMPT,
        )

        if not raw_result:
            logger.warning(
                "Certification LLM extraction returned empty output."
            )
            return []

        result = self._parse_result(
            raw_result
        )

        logger.debug(
            "Extracted {} certification records.",
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

        text = raw_result.strip()

        text = cls._remove_code_fence(
            text
        )

        parsed = cls._parse_json(
            text
        )

        if parsed is None:
            logger.warning(
                "Failed to parse certification LLM output as JSON."
            )

            logger.debug(
                "Certification LLM output preview: {}",
                text[:1000],
            )

            return []

        if isinstance(parsed, dict):

            certifications = parsed.get(
                "certifications",
                [],
            )

        elif isinstance(parsed, list):

            certifications = parsed

        else:
            return []

        if not isinstance(
            certifications,
            list,
        ):
            return []

        normalized: List[Dict[str, Any]] = []

        for item in certifications:

            if not isinstance(
                item,
                dict,
            ):
                continue

            entry = {
                "name": cls._normalize_string(
                    item.get("name")
                ),
                "issuer": cls._normalize_string(
                    item.get("issuer")
                ),
                "issue_date": cls._normalize_string(
                    item.get("issue_date")
                ),
                "expiry_date": cls._normalize_string(
                    item.get("expiry_date")
                ),
                "credential_id": cls._normalize_string(
                    item.get("credential_id")
                ),
                "credential_url": cls._normalize_string(
                    item.get("credential_url")
                ),
            }

            if not cls._has_content(
                entry
            ):
                continue

            normalized.append(
                entry
            )

        return normalized

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

    @classmethod
    def _parse_json(
        cls,
        text: str,
    ) -> Any | None:

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            pass

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
                return json.loads(
                    candidate
                )
            except json.JSONDecodeError:
                pass

        start = text.find("[")
        end = text.rfind("]")

        if (
            start >= 0
            and end > start
        ):
            candidate = text[
                start:end + 1
            ]

            try:
                return json.loads(
                    candidate
                )
            except json.JSONDecodeError:
                pass

        recovered = cls._recover_array_objects(
            text,
            "certifications",
        )

        if recovered:
            logger.warning(
                "LLM output appears truncated. Recovered {} "
                "complete certification object(s) out of a likely "
                "incomplete response.",
                len(recovered),
            )
            return recovered

        return None

    @staticmethod
    def _recover_array_objects(
        text: str,
        array_key: str,
    ) -> Optional[List[Dict[str, Any]]]:

        key_index = text.find(
            f'"{array_key}"'
        )

        if key_index < 0:
            return None

        array_start = text.find(
            "[",
            key_index,
        )

        if array_start < 0:
            return None

        objects: List[Dict[str, Any]] = []

        bracket_depth = 0
        brace_depth = 0

        object_start: Optional[int] = None

        in_string = False
        escaped = False

        for index in range(
            array_start,
            len(text),
        ):

            char = text[index]

            if in_string:

                if escaped:
                    escaped = False
                    continue

                if char == "\\":
                    escaped = True
                    continue

                if char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
                continue

            if char == "[":
                bracket_depth += 1
                continue

            if char == "]":
                bracket_depth -= 1

                if bracket_depth == 0:
                    break

                continue

            if char == "{":

                if (
                    brace_depth == 0
                    and bracket_depth == 1
                ):
                    object_start = index

                brace_depth += 1
                continue

            if char == "}":
                brace_depth -= 1

                if (
                    brace_depth == 0
                    and object_start is not None
                ):

                    candidate = text[
                        object_start:index + 1
                    ]

                    try:
                        parsed_object = json.loads(
                            candidate
                        )

                        if isinstance(
                            parsed_object,
                            dict,
                        ):
                            objects.append(
                                parsed_object
                            )

                    except json.JSONDecodeError:
                        pass

                    object_start = None

                continue

        return objects if objects else None

    @staticmethod
    def _normalize_string(
        value: Any,
    ) -> str | None:

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
    def _has_content(
        entry: Dict[str, Any],
    ) -> bool:

        return any(
            value is not None
            and str(value).strip()
            for value in entry.values()
        )