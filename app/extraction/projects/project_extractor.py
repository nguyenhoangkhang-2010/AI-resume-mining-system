import re
from typing import List, Dict, Any, Optional, Tuple

from loguru import logger

from app.extraction.ner.ner_service import NERService


class ProjectExtractor:

    BULLET_PATTERN = re.compile(
        r"^\s*(?:[-•●▪◦‣*]\s+|\d+[.)]\s+)"
    )

    DATE_RANGE_PATTERN = re.compile(
        r"""
        (?:
            \b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)
            (?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?
            \s+\d{4}
            |
            \b\d{4}
        )
        \s*
        (?:[-–—]|to|until)
        \s*
        (?:
            \b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)
            (?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?
            \s+\d{4}
            |
            \b(?:present|current|now)
            |
            \b\d{4}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    SINGLE_DATE_PATTERN = re.compile(
        r"""
        \b(?:
            jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec
        )
        (?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?
        \s+\d{4}\b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    SCORE_PATTERN = re.compile(
        r"""
        \b
        (?:
            final\s+score
            |
            score
            |
            grade
            |
            gpa
        )
        \s*[:=]?\s*
        \d+(?:\.\d+)?
        \s*(?:/\s*\d+(?:\.\d+)?)?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    RANK_PATTERN = re.compile(
        r"""
        \b
        (?:
            top\s+\d+
            |
            \d+(?:st|nd|rd|th)
            (?:\s+(?:place|project|team))?
        )
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    ROLE_PATTERN = re.compile(
        r"""
        \b
        (?:
            team\s+leader
            |
            project\s+leader
            |
            leader
            |
            member
        )
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    AWARD_PATTERN = re.compile(
        r"""
        \b
        (?:
            first\s+prize
            |
            second\s+prize
            |
            third\s+prize
            |
            consolation\s+prize
            |
            grand\s+prize
            |
            runner[-\s]?up
            |
            finalist
            |
            winner
        )
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    SUPPORTING_DOCUMENT_PATTERN = re.compile(
        r"""
        \b
        (?:
            supporting\s+document
            |
            attachment
            |
            appendix
            |
            link
        )
        \s*:
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    METADATA_PATTERNS = (
        SCORE_PATTERN,
        RANK_PATTERN,
        ROLE_PATTERN,
        AWARD_PATTERN,
        SUPPORTING_DOCUMENT_PATTERN,
    )

    def __init__(
        self,
        ner_service: Optional[NERService] = None,
    ) -> None:
        self.ner_service = ner_service or NERService()


    @staticmethod
    def _clean_line(line: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            line,
        ).strip()

    @classmethod
    def _is_bullet(cls, line: str) -> bool:
        return bool(
            cls.BULLET_PATTERN.match(line)
        )


    @classmethod
    def _extract_date(
        cls,
        line: str,
    ) -> Optional[str]:
        match = cls.DATE_RANGE_PATTERN.search(line)

        if match:
            return match.group(0).strip()

        match = cls.SINGLE_DATE_PATTERN.search(line)

        if match:
            return match.group(0).strip()

        return None

    @classmethod
    def _remove_date(
        cls,
        line: str,
    ) -> str:
        line = cls.DATE_RANGE_PATTERN.sub(
            "",
            line,
        )

        line = cls.SINGLE_DATE_PATTERN.sub(
            "",
            line,
        )

        return cls._clean_line(line)

    @classmethod
    def _extract_metadata(
        cls,
        line: str,
    ) -> Dict[str, str]:

        metadata: Dict[str, str] = {}

        score = cls.SCORE_PATTERN.search(line)
        if score:
            metadata["score"] = score.group(0)

        rank = cls.RANK_PATTERN.search(line)
        if rank:
            metadata["rank"] = rank.group(0)

        role = cls.ROLE_PATTERN.search(line)
        if role:
            metadata["role"] = role.group(0)

        award = cls.AWARD_PATTERN.search(line)
        if award:
            metadata["award"] = award.group(0)

        return metadata

    @classmethod
    def _is_metadata_line(
        cls,
        line: str,
    ) -> bool:

        if cls._extract_metadata(line):
            return True

        return bool(
            cls.SUPPORTING_DOCUMENT_PATTERN.search(line)
        )

    def _extract_entities(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:

        try:
            return self.ner_service.extract(text)
        except Exception as exc:
            logger.warning(
                f"NER failed during project extraction: {exc}"
            )
            return []

    @staticmethod
    def _entity_label(
        entity: Dict[str, Any],
    ) -> str:
        return str(
            entity.get("label", "")
        ).upper()

    @staticmethod
    def _entity_score(
        entity: Dict[str, Any],
    ) -> float:

        try:
            return float(
                entity.get("score", 0.0)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _entity_start(
        entity: Dict[str, Any],
    ) -> int:

        try:
            return int(
                entity.get("start", -1)
            )
        except (
            TypeError,
            ValueError,
        ):
            return -1

    @staticmethod
    def _entity_end(
        entity: Dict[str, Any],
    ) -> int:

        try:
            return int(
                entity.get("end", -1)
            )
        except (
            TypeError,
            ValueError,
        ):
            return -1

    def _title_candidates(
        self,
        line: str,
    ) -> List[Dict[str, Any]]:

        entities = self._extract_entities(line)

        candidates: List[Dict[str, Any]] = []

        for entity in entities:

            label = self._entity_label(entity)
            score = self._entity_score(entity)

            if label not in {
                "TITLE",
                "ORG",
            }:
                continue

            if score < 0.70:
                continue

            start = self._entity_start(entity)
            end = self._entity_end(entity)

            if start < 0 or end <= start:
                continue

            value = line[start:end].strip()

            if not value:
                continue

            value = self._clean_line(value)

            if not value:
                continue

            candidates.append(
                {
                    "text": value,
                    "label": label,
                    "score": score,
                    "start": start,
                    "end": end,
                }
            )

        return candidates

    def _extract_title_from_header(
        self,
        header: str,
    ) -> Optional[str]:

        header = self._clean_line(header)

        if not header:
            return None

        candidates = self._title_candidates(
            header
        )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item["label"] == "TITLE",
                item["score"],
                len(item["text"]),
            ),
            reverse=True,
        )

        best = candidates[0]

        title = best["text"]

        title = title.strip(
            "\"“”'`:-–— "
        )

        if not title:
            return None

        return title

    def _analyze_header(
        self,
        line: str,
    ) -> Optional[Dict[str, Any]]:

        date = self._extract_date(line)

        if not date:
            return None

        date_match = (
            self.DATE_RANGE_PATTERN.search(line)
            or self.SINGLE_DATE_PATTERN.search(line)
        )

        if not date_match:
            return None

        before_date = self._clean_line(
            line[:date_match.start()]
        )

        after_date = self._clean_line(
            line[date_match.end():]
        )

        if not before_date:
            return None

        title = self._extract_title_from_header(
            before_date
        )

        if not title:
            return None

        return {
            "title": title,
            "date": date,
            "before_date": before_date,
            "after_date": after_date,
        }

    def _header_score(
        self,
        line: str,
    ) -> float:

        score = 0.0

        if self._is_bullet(line):
            return -1.0

        if self._is_metadata_line(line):
            return -1.0

        if self._extract_date(line):
            score += 0.45

        entities = self._title_candidates(line)

        if entities:
            score += 0.35

        word_count = len(line.split())

        if 2 <= word_count <= 20:
            score += 0.10

        if word_count > 30:
            score -= 0.20

        return score

    def _is_project_header(
        self,
        line: str,
    ) -> bool:

        analysis = self._analyze_header(
            line
        )

        if analysis:
            return True

        if self._header_score(line) >= 0.70:
            candidates = self._title_candidates(
                line
            )

            return bool(candidates)

        return False

    @staticmethod
    def _new_project(
        title: str,
    ) -> Dict[str, Any]:

        return {
            "name": title,
            "description": [],
        }

    @classmethod
    def _append_description(
        cls,
        project: Dict[str, Any],
        line: str,
    ) -> None:

        clean = re.sub(
            r"^\s*[-•●▪◦‣*]\s*",
            "",
            line,
        )

        clean = cls._clean_line(
            clean
        )

        if clean:
            project.setdefault(
                "description",
                [],
            ).append(clean)

    def _start_project_from_header(
        self,
        line: str,
    ) -> Optional[Dict[str, Any]]:

        analysis = self._analyze_header(
            line
        )

        if not analysis:
            return None

        project = self._new_project(
            analysis["title"]
        )

        metadata = project.setdefault(
            "metadata",
            {},
        )

        metadata["date"] = analysis[
            "date"
        ]

        if analysis["after_date"]:
            self._append_description(
                project,
                analysis["after_date"],
            )

        return project

    def _parse_lines(
        self,
        lines: List[str],
    ) -> List[Dict[str, Any]]:

        projects: List[
            Dict[str, Any]
        ] = []

        current_project: Optional[
            Dict[str, Any]
        ] = None

        for raw_line in lines:

            line = self._clean_line(
                raw_line
            )

            if not line:
                continue

            if self._is_bullet(line):

                if current_project:
                    self._append_description(
                        current_project,
                        line,
                    )

                continue

            if self._is_metadata_line(line):

                if current_project is None:
                    continue

                metadata = current_project.setdefault(
                    "metadata",
                    {},
                )

                extracted = (
                    self._extract_metadata(
                        line
                    )
                )

                metadata.update(
                    extracted
                )

                if (
                    not extracted
                    and self.SUPPORTING_DOCUMENT_PATTERN.search(
                        line
                    )
                ):
                    self._append_description(
                        current_project,
                        line,
                    )

                continue

            if self._is_project_header(line):

                project = (
                    self._start_project_from_header(
                        line
                    )
                )

                if project is not None:

                    if current_project is not None:
                        projects.append(
                            current_project
                        )

                    current_project = project

                    continue

            date = self._extract_date(
                line
            )

            if date and current_project:

                current_project.setdefault(
                    "metadata",
                    {},
                )["date"] = date

                remainder = self._remove_date(
                    line
                )

                if remainder:
                    self._append_description(
                        current_project,
                        remainder,
                    )

                continue

            if current_project is not None:

                self._append_description(
                    current_project,
                    line,
                )

        if current_project is not None:
            projects.append(
                current_project
            )

        return projects

    def extract(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:

        if not text:
            return []

        logger.debug(
            "Starting project extraction."
        )

        lines = [
            line
            for line in text.splitlines()
            if line.strip()
        ]

        projects = self._parse_lines(
            lines
        )

        logger.debug(
            f"Extracted projects: {len(projects)}"
        )

        return projects