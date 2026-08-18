from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.extraction.llm.llm_extractor import LLMExtractor


class SectionClassifier:

    CANONICAL_SECTION_TYPES = {
        "personal_info",
        "summary",
        "education",
        "experience",
        "projects",
        "certifications",
        "skills",
        "other",
    }

    def __init__(
        self,
        llm_extractor: Optional[LLMExtractor] = None,
    ) -> None:
        self.llm_extractor = (
            llm_extractor
            if llm_extractor is not None
            else LLMExtractor()
        )

    def classify_document(
        self,
        lines: List[str],
    ) -> List[Dict[str, Any]]:

        if not lines:
            return []

        candidate_lines = self._find_candidate_headings(lines)

        logger.info(
            "Structural heading detection found {} candidate lines",
            len(candidate_lines),
        )

        document = self._build_candidate_document(
            lines=lines,
            candidates=candidate_lines,
        )

        prompt = self._build_candidate_prompt()

        try:
            response = self.llm_extractor.extract_info(
                document,
                prompt,
                max_new_tokens=256,
            )

            logger.debug(
                "Raw candidate section classification response: {}",
                response,
            )

            results = self._parse_document_response(
                response,
            )

            results = self._validate_line_indices(
                results,
                lines,
            )

            results = self._validate_boundaries(
                results,
                lines,
            )

            logger.info(
                "Candidate section classification returned {} sections",
                len(results),
            )

            return results

        except Exception as exc:
            logger.warning(
                "Candidate section classification failed: {}",
                exc,
            )
            return []

    def classify_single(
        self,
        text: str,
    ) -> Tuple[str, float]:
        """
        Classify a single small fragment of text (e.g. one semantic
        region) into one of the canonical section categories.

        This is a lightweight fallback used when the fast embedding
        classifier (SectionSemanticClassifier) is not confident enough
        about a given region. It uses a short, focused prompt instead
        of the full-document classification prompt, so it stays fast
        even though it still goes through the LLM.
        """

        if not text or not text.strip():
            return "other", 0.0

        prompt = self._build_single_prompt()

        try:
            response = self.llm_extractor.extract_info(
                text,
                prompt,
                max_new_tokens=32,
            )

            logger.debug(
                "Raw single-region classification response: {}",
                response,
            )

            return self._parse_single_response(response)

        except Exception as exc:
            logger.warning(
                "Single-region LLM classification failed: {}",
                exc,
            )
            return "other", 0.0

    @classmethod
    def _find_candidate_headings(
        cls,
        lines: List[str],
    ) -> List[Dict[str, Any]]:

        candidates: List[Dict[str, Any]] = []

        for index, line in enumerate(lines):

            if cls._looks_like_heading(
                line=line,
                index=index,
                lines=lines,
            ):
                candidates.append(
                    {
                        "line_index": index,
                        "heading": line,
                    }
                )

        return candidates

    @staticmethod
    def _looks_like_heading(
        line: str,
        index: int,
        lines: List[str],
    ) -> bool:

        text = line.strip()

        if not text:
            return False

        words = text.split()

        if not words:
            return False

        if len(words) > 8:
            return False

        if re.match(
            r"^\s*(?:[-•●▪◦‣*]|\d+[.)])\s+",
            text,
        ):
            return False

        if text.endswith(
            (
                ".",
                ",",
                ";",
                ":",
                "!",
                "?",
            )
        ):
            return False

        lowered = text.casefold()

        if any(
            marker in lowered
            for marker in (
                "@",
                "http://",
                "https://",
                "linkedin.com",
                "github.com",
            )
        ):
            return False

        if any(
            marker in text
            for marker in (
                "|",
                "(",
                ")",
                "/",
            )
        ):
            return False

        if re.search(
            r"\b(?:19|20)\d{2}\b",
            text,
        ):
            return False

        digit_count = sum(
            char.isdigit()
            for char in text
        )

        if digit_count > 0:
            return False

        alphabetic_chars = [
            char
            for char in text
            if char.isalpha()
        ]

        if alphabetic_chars:

            uppercase_ratio = (
                sum(
                    char.isupper()
                    for char in alphabetic_chars
                )
                / len(alphabetic_chars)
            )

            if uppercase_ratio >= 0.80:
                return True

        if not (
            1 <= len(words) <= 5
            and index > 0
            and index < len(lines) - 1
        ):
            return False

        previous = lines[index - 1].strip()
        following = lines[index + 1].strip()

        if not previous or not following:
            return False

        title_case_words = sum(
            word[:1].isupper()
            for word in words
            if word
        )

        if title_case_words != len(words):
            return False

        previous_words = previous.split()
        following_words = following.split()

        if len(previous_words) > 8:
            return True

        if len(following_words) > 8:
            return True

        return False

    @staticmethod
    def _build_candidate_document(
        lines: List[str],
        candidates: List[Dict[str, Any]],
    ) -> str:

        candidate_indices = {
            item["line_index"]
            for item in candidates
        }

        output: List[str] = []

        context_limit = min(
            len(lines),
            12,
        )

        for index in range(context_limit):
            marker = (
                "CANDIDATE_HEADING"
                if index in candidate_indices
                else "DOCUMENT_LINE"
            )

            output.append(
                f"[{index}] [{marker}] {lines[index]}"
            )

        for item in candidates:
            index = item["line_index"]

            if index < context_limit:
                continue

            output.append(
                f"[{index}] [CANDIDATE_HEADING] "
                f"{item['heading']}"
            )

        return "\n".join(output)

    @staticmethod
    def _build_candidate_prompt() -> str:

        return """
    You are a semantic document-structure classifier for resumes and CVs.

    Your task is to identify the top-level semantic regions of the resume
    and classify each one into a canonical category.

    The input contains:
    - document lines
    - structurally detected candidate headings
    - surrounding document context

    You must reason from the actual document content and structure.

    IMPORTANT:

    A semantic section does NOT always require an explicit heading.

    Some resume regions may be implicit.
    For example, information appearing before the first explicit
    section heading may form a personal-information region.

    When such an implicit region exists, create a section boundary
    at its first line.

    Do NOT invent a heading for an implicit region.
    Use an empty string for "heading" and set "implicit" to true.

    For explicit section boundaries:
    - keep the exact line_index
    - keep the exact heading text
    - infer the semantic category from the document content, NOT from
    literal keyword matching against the heading text

    For implicit boundaries:
    - use the first line belonging to the semantic region
    - set heading to ""
    - set implicit to true

    Do NOT classify these as separate sections merely because
    they look like standalone resume content:

    - person names
    - organization names
    - job titles
    - project titles
    - course names
    - certification names
    - award names
    - individual achievements
    - ordinary content

    Instead, determine whether they belong to a larger semantic region.

    CANONICAL CATEGORIES:

    Every section_type MUST be exactly one of the following canonical
    values, regardless of the original heading's wording or language:

    - personal_info
    - summary
    - education
    - experience
    - projects
    - certifications
    - skills
    - other

    Rules for classification:

    - Base your decision on the SEMANTIC MEANING and CONTENT of the
    region, not on literal keyword matching.
    - The original heading may be written in any language, may use a
    synonym, a translation, or an unconventional phrasing
    (for example: "Personal Projects", "Academic Projects",
    "Dự án cá nhân", "Projets", "Selected Work" all map to "projects";
    "Work Experience", "Kinh nghiệm làm việc", "Career History" all
    map to "experience").
    - Use "other" only when the region clearly does not belong to any
    of the categories above (e.g. hobbies, references, languages
    spoken, additional information).
    - Never invent a category outside this fixed list.

    Return all meaningful top-level semantic section boundaries
    that can be inferred from the provided document.

    Return them in ascending line_index order.

    Required JSON format:

    [
    {
        "line_index": 0,
        "heading": "",
        "section_type": "personal_info",
        "confidence": 0.99,
        "implicit": true
    },
    {
        "line_index": 2,
        "heading": "CAREER OBJECTIVE",
        "section_type": "summary",
        "confidence": 1.0,
        "implicit": false
    }
    ]

    Rules:

    - line_index must refer to the actual input line.
    - heading must exactly match the source line for explicit sections.
    - heading must be "" for implicit sections.
    - section_type must be one of the canonical categories listed above.
    - confidence must be between 0 and 1.
    - implicit must be either true or false.
    - Do not return duplicate line_index values.
    - Do not return explanations.
    - Do not return markdown.
    - Do not return code fences.
    - Return ONLY the JSON array.

DOCUMENT:
""".strip()

    @staticmethod
    def _build_single_prompt() -> str:

        return """
    You are a semantic classifier for a single fragment of a resume.

    Classify the CONTENT below into exactly ONE of the following
    canonical categories, based on its semantic meaning, regardless
    of language, wording, or original heading text:

    - personal_info
    - summary
    - education
    - experience
    - projects
    - certifications
    - skills
    - other

    Return ONLY a JSON object in this exact format, nothing else,
    no explanations, no markdown, no code fences:

    {"section_type": "projects", "confidence": 0.93}

CONTENT:
""".strip()

    @staticmethod
    def _parse_single_response(
        response: str,
    ) -> Tuple[str, float]:

        if not response:
            return "other", 0.0

        text = response.strip()

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
        ).strip()

        data: Dict[str, Any] = {}

        try:
            data = json.loads(text)

        except json.JSONDecodeError:

            match = re.search(
                r'"section_type"\s*:\s*"([^"]+)"',
                text,
            )

            if not match:
                return "other", 0.0

            confidence_match = re.search(
                r'"confidence"\s*:\s*([0-9.]+)',
                text,
            )

            data = {
                "section_type": match.group(1),
                "confidence": (
                    confidence_match.group(1)
                    if confidence_match
                    else 0.5
                ),
            }

        section_type = str(
            data.get(
                "section_type",
                "",
            )
        ).strip().casefold()

        if section_type not in SectionClassifier.CANONICAL_SECTION_TYPES:
            section_type = "other"

        try:
            confidence = float(
                data.get(
                    "confidence",
                    0.5,
                )
            )

        except (TypeError, ValueError):
            confidence = 0.5

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        return section_type, confidence

    @staticmethod
    def _parse_document_response(
        response: str,
    ) -> List[Dict[str, Any]]:

        if not response:
            return []

        text = response.strip()

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
        ).strip()

        try:
            data = json.loads(text)

            return SectionClassifier._validate_document_result(
                data,
            )

        except json.JSONDecodeError:
            pass

        # Recover complete JSON objects from truncated output.
        recovered: List[Dict[str, Any]] = []

        object_pattern = re.compile(
            r"""
            \{
                \s*"line_index"\s*:\s*(-?\d+)
                \s*,\s*"heading"\s*:\s*"([^"]*)"
                \s*,\s*"section_type"\s*:\s*"([^"]*)"
                \s*,\s*"confidence"\s*:\s*([0-9.]+)
                (?:\s*,\s*"implicit"\s*:\s*(true|false))?
                \s*\}
            """,
            flags=re.VERBOSE | re.IGNORECASE,
        )

        for match in object_pattern.finditer(text):

            try:
                recovered.append(
                    {
                        "line_index": int(
                            match.group(1)
                        ),
                        "heading": match.group(2),
                        "section_type": match.group(3),
                        "confidence": float(
                            match.group(4)
                        ),
                        "implicit": (
                            match.group(5).lower() == "true"
                            if match.group(5)
                            else False
                        ),
                    }
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        if recovered:
            logger.warning(
                "Recovered {} complete section objects from incomplete LLM JSON.",
                len(recovered),
            )

        return SectionClassifier._validate_document_result(
            recovered,
        )

    @staticmethod
    def _validate_document_result(
        data: Any,
    ) -> List[Dict[str, Any]]:

        if not isinstance(data, list):
            return []

        results: List[Dict[str, Any]] = []

        for item in data:

            if not isinstance(item, dict):
                continue

            line_index = item.get("line_index")

            if not isinstance(line_index, int):
                continue

            if line_index < 0:
                continue

            heading = item.get("heading", "")

            if not isinstance(heading, str):
                continue

            heading = heading.strip()

            section_type = item.get("section_type")

            if not isinstance(section_type, str):
                continue

            section_type = " ".join(
                section_type.strip().split()
            ).casefold()

            if section_type not in SectionClassifier.CANONICAL_SECTION_TYPES:
                logger.warning(
                    "LLM returned non-canonical section_type '{}' at "
                    "line {}. Falling back to 'other'.",
                    section_type,
                    line_index,
                )
                section_type = "other"

            if not section_type:
                continue

            confidence = item.get(
                "confidence",
                0.0,
            )

            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 0.0

            confidence = max(
                0.0,
                min(1.0, confidence),
            )

            implicit = item.get(
                "implicit",
                False,
            )

            if not isinstance(implicit, bool):
                implicit = False

            if not implicit and not heading:
                continue

            if implicit:
                heading = ""

            results.append(
                {
                    "line_index": line_index,
                    "heading": heading,
                    "section_type": section_type,
                    "confidence": confidence,
                    "implicit": implicit,
                }
            )

        return results

    @staticmethod
    def _validate_boundaries(
        results: List[Dict[str, Any]],
        lines: List[str],
    ) -> List[Dict[str, Any]]:

        if not results:
            return []

        validated: List[Dict[str, Any]] = []

        results = sorted(
            results,
            key=lambda item: item["line_index"],
        )

        for item in results:

            index = item["line_index"]

            if index < 0 or index >= len(lines):
                continue

            implicit = bool(
                item.get("implicit", False)
            )

            if implicit:
                item["heading"] = ""
                validated.append(item)
                continue

            heading = item.get(
                "heading",
                "",
            ).strip()

            if not heading:
                logger.warning(
                    "Removing explicit boundary at line {} "
                    "because heading is empty.",
                    index,
                )
                continue

            if not SectionClassifier._looks_like_heading(
                line=lines[index],
                index=index,
                lines=lines,
            ):
                logger.warning(
                    "Removing non-structural boundary at line {}: '{}'",
                    index,
                    lines[index],
                )
                continue

            item["heading"] = lines[index]

            validated.append(item)

        validated = SectionClassifier._remove_nested_boundaries(
            validated,
            lines,
        )

        validated.sort(
            key=lambda item: item["line_index"]
        )

        return validated

    @staticmethod
    def _remove_nested_boundaries(
        results: List[Dict[str, Any]],
        lines: List[str],
    ) -> List[Dict[str, Any]]:

        if len(results) <= 1:
            return results

        validated: List[Dict[str, Any]] = []

        for item in results:

            if not validated:
                validated.append(item)
                continue

            previous = validated[-1]

            current_index = item["line_index"]
            previous_index = previous["line_index"]

            current_type = (
                item.get("section_type", "")
                .strip()
                .casefold()
            )

            previous_type = (
                previous.get("section_type", "")
                .strip()
                .casefold()
            )

            if (
                current_type
                and previous_type
                and (
                    current_type == previous_type
                    or current_type.startswith(
                        previous_type + "_"
                    )
                    or previous_type.startswith(
                        current_type + "_"
                    )
                )
            ):
                logger.warning(
                    "Removing nested section boundary at line {} "
                    "('{}') because it belongs to the same semantic "
                    "region as line {} ('{}').",
                    current_index,
                    lines[current_index],
                    previous_index,
                    previous_type,
                )
                continue

            if not bool(item.get("implicit", False)):

                heading = lines[current_index].strip()

                if not SectionClassifier._looks_like_heading(
                    line=heading,
                    index=current_index,
                    lines=lines,
                ):
                    logger.warning(
                        "Removing nested content boundary at line {}: '{}'",
                        current_index,
                        heading,
                    )
                    continue

            validated.append(item)

        return validated

    @staticmethod
    def _validate_line_indices(
        results: List[Dict[str, Any]],
        lines: List[str],
    ) -> List[Dict[str, Any]]:

        validated: List[Dict[str, Any]] = []

        seen = set()

        for item in results:

            index = item["line_index"]

            if index >= len(lines):
                continue

            if index in seen:
                continue

            implicit = bool(
                item.get("implicit", False)
            )

            if implicit:
                item["heading"] = ""
            else:
                item["heading"] = lines[index]

            validated.append(item)
            seen.add(index)

        validated.sort(
            key=lambda item: item["line_index"]
        )

        return validated