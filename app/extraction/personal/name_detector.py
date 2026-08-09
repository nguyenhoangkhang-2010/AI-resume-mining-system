from pathlib import Path
import json

from app.extraction.ner.ner_service import NERService


class NameDetector:

    def __init__(self):
        path = (
            Path(__file__)
            .parent
            .parent
            / "config"
            / "extraction_rules.json"
        )

        with open(
            path,
            encoding="utf-8",
        ) as f:
            self.rules = json.load(f)

        self.ner_service = NERService()

    def detect(self, text: str):
        if not text:
            return None

        name = self._detect_from_header(text)

        if name:
            return name

        return self._detect_from_ner(text)

    def _detect_from_header(self, text: str):
        lines = self._prepare_lines(text)

        scan_lines = self.rules["name"].get(
            "scan_lines",
            5,
        )

        candidates = []

        for line_index, line in enumerate(
            lines[:scan_lines]
        ):
            if not self.valid(line):
                continue

            person_entities = self._get_person_entities(
                line
            )

            for entity in person_entities:
                entity_text = entity.get(
                    "text",
                    "",
                ).strip()

                if not entity_text:
                    continue

                score = self._header_candidate_score(
                    line=line,
                    line_index=line_index,
                    entity=entity,
                )

                candidates.append(
                    (
                        entity_text,
                        score,
                        entity,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return candidates[0][0]

    def _header_candidate_score(
        self,
        line: str,
        line_index: int,
        entity: dict,
    ) -> float:

        entity_text = entity.get(
            "text",
            "",
        ).strip()

        if not entity_text:
            return float("-inf")

        score = 0.0

        line_normalized = " ".join(
            line.split()
        ).casefold()

        entity_normalized = " ".join(
            entity_text.split()
        ).casefold()

        if entity_normalized == line_normalized:
            score += 5.0

        elif entity_normalized in line_normalized:
            score += 2.0

        line_length = max(
            1,
            len(line_normalized),
        )

        coverage = min(
            1.0,
            len(entity_normalized) / line_length,
        )

        score += coverage * 4.0

        score += max(
            0.0,
            2.0 - line_index * 0.5,
        )

        try:
            score += float(
                entity.get(
                    "score",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

        try:
            agreement = int(
                entity.get(
                    "model_agreement",
                    1,
                )
            )

            score += min(
                2.0,
                agreement * 0.75,
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

        if entity.get("label") == "PERSON":
            score += 2.0

        return score

    def _get_person_entities(
        self,
        text: str,
    ) -> list[dict]:

        try:
            entities = self.ner_service.extract(
                text
            )
        except Exception:
            return []

        return [
            entity
            for entity in entities
            if entity.get("label") == "PERSON"
        ]

    def _detect_from_ner(self, text: str):
        try:
            entities = self.ner_service.extract(
                text
            )

            candidates = []

            for entity in entities:
                if entity.get("label") != "PERSON":
                    continue

                value = entity.get(
                    "text",
                    "",
                ).strip()

                if not value:
                    continue

                if not self.valid(value):
                    continue

                score = self._candidate_score(
                    value,
                    entity,
                )

                candidates.append(
                    (
                        value,
                        score,
                    )
                )

            if not candidates:
                return None

            candidates.sort(
                key=lambda item: item[1],
                reverse=True,
            )

            return candidates[0][0]

        except Exception:
            return None

    def _candidate_score(
        self,
        text: str,
        entity: dict,
    ) -> float:

        score = 0.0

        words = text.split()

        if 2 <= len(words) <= 4:
            score += 2.0

        if all(
            word[:1].isupper()
            for word in words
            if word
        ):
            score += 2.0

        raw_label = entity.get(
            "raw_label"
        )

        if raw_label == "NAME":
            score += 5.0

        source = entity.get(
            "source"
        )

        if source == "primary":
            score += 3.0
        elif source == "multilingual":
            score += 0.5

        try:
            score += float(
                entity.get(
                    "score",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

        return score

    def _prepare_lines(
        self,
        text: str,
    ) -> list[str]:

        lines = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            parts = line.split("|")

            for part in parts:
                candidate = part.strip()

                if candidate:
                    lines.append(candidate)

        return lines

    def valid(
        self,
        line: str,
    ) -> bool:

        words = line.split()

        name_rules = self.rules["name"]

        min_words = name_rules["min_words"]
        max_words = name_rules["max_words"]
        max_length = name_rules["max_length"]

        if not (
            min_words
            <= len(words)
            <= max_words
        ):
            return False

        if len(line) > max_length:
            return False

        if any(
            char.isdigit()
            for char in line
        ):
            return False

        if "@" in line:
            return False

        if "http" in line.lower():
            return False

        if any(
            char in line
            for char in "[]()<>"
        ):
            return False

        return True