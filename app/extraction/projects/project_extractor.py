from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from loguru import logger

from app.extraction.llm.llm_extractor import LLMExtractor


class ProjectExtractor:

    EXTRACTION_PROMPT = """
    You are a multilingual resume information extraction system.

    Extract structured project information from the provided resume section.

    The input may contain:

    - academic projects
    - personal projects
    - university projects
    - research projects
    - software projects
    - engineering projects
    - data or AI projects
    - business projects
    - freelance projects
    - team projects
    - individual projects
    - projects written in different languages
    - projects without explicit dates
    - projects with different layouts
    - projects where metadata is mixed with descriptions

    Infer the semantic structure from the actual source text.

    Do NOT rely on:

    - fixed project names
    - fixed project categories
    - fixed technologies
    - fixed industries
    - fixed job titles
    - fixed company names
    - fixed university names
    - fixed award names
    - fixed keywords
    - fixed resume templates
    - fixed section layouts

    Do NOT assume that a project must contain a particular field.

    Return ONLY valid JSON.
    Do not use Markdown.
    Do not use ``` fences.
    Do not add explanations before or after the JSON.
    Do not repeat the input text outside the JSON.

    Expected structure:

    {
        "projects": [
            {
                "title": null,
                "description": [],
                "start_date": null,
                "end_date": null,
                "role": null,
                "team_size": null,
                "technologies": [],
                "responsibilities": [],
                "achievements": [],
                "url": null,
                "metadata": {}
            }
        ]
    }

    Rules:

    1. "title":
    Extract the semantic project title when one is identifiable.
    Preserve the original title from the source text.
    Do not invent a title.

    2. "description":
    Extract the project's general purpose, context, scope,
    functionality, objectives, or other descriptive information.
    Preserve meaningful information from the source.
    Return multiple items when appropriate.

    3. "start_date":
    Extract the project starting date when available.
    Preserve the original date representation when possible.

    4. "end_date":
    Extract the project ending date when available.
    Preserve the original date representation when possible.
    If the project is explicitly ongoing, preserve the semantic
    ongoing representation instead of inventing a date.

    5. "role":
    Extract the candidate's role or contribution in the project
    only when the source text supports it.
    Do not infer a role merely because the candidate participated.

    6. "team_size":
    Extract team size only when explicitly stated or clearly
    represented in the source text.
    Do not infer team size from the number of contributors.

    7. "technologies":
    Extract technologies, tools, frameworks, platforms, methods,
    or technical resources explicitly associated with the project.
    Preserve the original wording whenever possible.
    Do not generate technologies from general knowledge.

    8. "responsibilities":
    Extract concrete responsibilities or activities performed
    by the candidate.
    Do not convert project descriptions into responsibilities
    unless the source supports that interpretation.

    9. "achievements":
    Extract measurable or explicitly stated project outcomes,
    results, awards, rankings, improvements, performance results,
    or other accomplishments.
    Do not convert ordinary responsibilities into achievements.

    10. "url":
    Extract a project URL, repository URL, demo URL, or other
    project-specific link when available.
    Do not extract unrelated personal or social-media links.

    11. "metadata":
    Preserve additional project-specific information that is
    clearly associated with the project but does not fit the
    canonical fields above.

    Metadata must be semantic and source-derived.

    12. Multiple distinct projects must produce multiple objects.

    13. Do not merge separate projects merely because they share
    technologies, institutions, organizations, dates, or people.

    14. Do not split one project into multiple projects merely
    because it contains multiple paragraphs or bullet points.

    15. Do not fabricate missing information.

    16. If a field cannot be confidently extracted:
    - scalar fields -> null
    - list fields -> []
    - metadata -> {}

    17. Preserve the original meaning and wording whenever possible.

    18. The input may be multilingual.
    Interpret semantic meaning regardless of language.

    19. Do not translate extracted values unless necessary for
    semantic interpretation.

    20. Do not normalize project titles, technologies, roles,
    organizations, awards, or other entities against hard-coded
    dictionaries.

    21. The extractor must remain generic and extensible.

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
        section_type: str | None = None,
    ) -> List[Dict[str, Any]]:

        if not text or not text.strip():
            return []

        logger.debug(
            "Starting semantic project extraction."
        )

        raw_result = self.llm_extractor.extract_info(
            text=text,
            prompt_template=self.EXTRACTION_PROMPT,
            max_new_tokens=768,
        )

        if not raw_result:
            logger.warning(
                "Project LLM extraction returned empty output."
            )
            return []

        logger.debug(
            "Project LLM raw output length: {} characters.",
            len(raw_result),
        )

        result = self._parse_result(
            raw_result
        )

        logger.debug(
            "Extracted {} project records.",
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

        text = cls._remove_markdown_code_fence(
            text
        )

        parsed = cls._parse_json(
            text
        )

        if parsed is None:
            logger.warning(
                "Failed to parse project LLM output as JSON."
            )

            logger.debug(
                "Project LLM output preview: {}",
                text[:1000],
            )

            return []

        projects = cls._extract_projects(
            parsed
        )

        if not projects:
            return []

        normalized: List[Dict[str, Any]] = []

        for item in projects:

            if not isinstance(
                item,
                dict,
            ):
                continue

            entry = {
                "title": cls._normalize_string(
                    item.get("title")
                ),
                "description": cls._normalize_string_list(
                    item.get("description")
                ),
                "start_date": cls._normalize_string(
                    item.get("start_date")
                ),
                "end_date": cls._normalize_string(
                    item.get("end_date")
                ),
                "role": cls._normalize_string(
                    item.get("role")
                ),
                "team_size": cls._normalize_team_size(
                    item.get("team_size")
                ),
                "technologies": cls._normalize_string_list(
                    item.get("technologies")
                ),
                "responsibilities": cls._normalize_string_list(
                    item.get("responsibilities")
                ),
                "achievements": cls._normalize_string_list(
                    item.get("achievements")
                ),
                "url": cls._normalize_string(
                    item.get("url")
                ),
                "metadata": cls._normalize_metadata(
                    item.get("metadata")
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
    def _extract_projects(
        parsed: Any,
    ) -> List[Any]:

        if isinstance(
            parsed,
            list,
        ):
            return parsed

        if not isinstance(
            parsed,
            dict,
        ):
            return []

        projects = parsed.get(
            "projects"
        )

        if isinstance(
            projects,
            list,
        ):
            return projects

        if isinstance(
            projects,
            dict,
        ):
            return [projects]

        if any(
            key in parsed
            for key in (
                "title",
                "description",
                "start_date",
                "end_date",
                "role",
                "technologies",
                "responsibilities",
                "achievements",
            )
        ):
            return [parsed]

        return []

    @staticmethod
    def _remove_markdown_code_fence(
        text: str,
    ) -> str:

        text = text.strip()

        if not text.startswith(
            "```"
        ):
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

        if not text:
            return None

        try:
            return json.loads(
                text
            )
        except json.JSONDecodeError:
            pass

        cleaned = cls._strip_code_fence(
            text
        )

        if cleaned != text:

            try:
                return json.loads(
                    cleaned
                )
            except json.JSONDecodeError:
                pass

        candidate = cls._extract_balanced_json(
            text,
            "{",
            "}",
        )

        if candidate:

            try:
                return json.loads(
                    candidate
                )
            except json.JSONDecodeError:
                pass

        candidate = cls._extract_balanced_json(
            text,
            "[",
            "]",
        )

        if candidate:

            try:
                return json.loads(
                    candidate
                )
            except json.JSONDecodeError:
                pass

        object_start = text.find(
            "{"
        )
        object_end = text.rfind(
            "}"
        )

        if (
            object_start >= 0
            and object_end > object_start
        ):

            candidate = text[
                object_start:object_end + 1
            ]

            try:
                return json.loads(
                    candidate
                )
            except json.JSONDecodeError:
                pass

        recovered = cls._recover_array_objects(
            text,
            "projects",
        )

        if recovered:
            logger.warning(
                "LLM output appears truncated. Recovered {} "
                "complete project object(s) out of a likely "
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
    def _strip_code_fence(
        text: str,
    ) -> str:

        text = text.strip()

        text = re.sub(
            r"^\s*```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```\s*$",
            "",
            text,
        )

        return text.strip()

    @staticmethod
    def _extract_balanced_json(
        text: str,
        opening: str,
        closing: str,
    ) -> str | None:

        start = text.find(
            opening
        )

        if start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False

        for index in range(
            start,
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

            if char == opening:
                depth += 1

            elif char == closing:
                depth -= 1

                if depth == 0:
                    return text[
                        start:index + 1
                    ]

        return None

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

        return value or None

    @staticmethod
    def _normalize_string_list(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):

            value = value.strip()

            return (
                [value]
                if value
                else []
            )

        if not isinstance(
            value,
            list,
        ):
            return []

        result: List[str] = []

        for item in value:

            if not isinstance(
                item,
                str,
            ):
                continue

            item = item.strip()

            if item:
                result.append(
                    item
                )

        return result

    @staticmethod
    def _normalize_team_size(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return None

        if isinstance(
            value,
            int,
        ):
            return value

        if isinstance(
            value,
            float,
        ):

            if value.is_integer():
                return int(
                    value
                )

            return None

        if isinstance(
            value,
            str,
        ):

            value = value.strip()

            if not value:
                return None

            if value.isdigit():
                return int(value)

            match = re.fullmatch(
                r"\s*(\d+)"
                r"(?:\s+.*)?",
                value,
            )

            if match:
                return int(
                    match.group(1)
                )

        return None

    @staticmethod
    def _normalize_metadata(
        value: Any,
    ) -> Dict[str, Any]:

        if not isinstance(
            value,
            dict,
        ):
            return {}

        result: Dict[str, Any] = {}

        for key, item in value.items():

            if not isinstance(
                key,
                str,
            ):
                continue

            key = key.strip()

            if not key:
                continue

            if isinstance(
                item,
                (
                    str,
                    int,
                    float,
                    bool,
                ),
            ):

                if (
                    isinstance(
                        item,
                        str,
                    )
                    and not item.strip()
                ):
                    continue

                result[key] = item

            elif isinstance(
                item,
                list,
            ):

                cleaned = []

                for element in item:

                    if not isinstance(
                        element,
                        str,
                    ):
                        continue

                    element = element.strip()

                    if element:
                        cleaned.append(
                            element
                        )

                if cleaned:
                    result[key] = cleaned

        return result

    @staticmethod
    def _has_content(
        entry: Dict[str, Any],
    ) -> bool:

        for key, value in entry.items():

            if key == "metadata":

                if value:
                    return True

                continue

            if isinstance(
                value,
                list,
            ):

                if value:
                    return True

            elif value is not None:

                if str(
                    value
                ).strip():
                    return True

        return False