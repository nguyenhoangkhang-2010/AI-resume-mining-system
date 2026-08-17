from typing import Dict, List, Optional

from loguru import logger
from app.extraction.skills.strategies.matching_strategy import (
    MatchingStrategy,
)
from app.extraction.skills.aggregation.result_aggregator import (
    ResultAggregator,
)
from app.extraction.skills.filters.confidence_filter import (
    ConfidenceFilter,
)
from app.extraction.skills.formatters.skill_formatter import (
    SkillFormatter,
)

from app.extraction.skills.bootstrap import (
    build_skill_normalizer,
)


class SkillExtractionPipeline:

    NON_SKILL_LABELS = {
        "PERSON",
        "ORG",
        "LOC",
        "DATE",
        "EMAIL",
        "PHONE",
        "TITLE",
    }

    def __init__(
        self,
        strategy: MatchingStrategy,
        ner_service=None,
    ):
        self.strategy = strategy
        self.aggregator = ResultAggregator()
        self.filter = ConfidenceFilter()
        self.normalizer = build_skill_normalizer()
        self.ner_service = ner_service

    def extract(self, text):

        logger.debug(
            "Starting skill extraction pipeline."
        )

        scan_text = self._mask_non_skill_entities(
            text
        )

        matches = self.strategy.extract(
            scan_text
        )

        filtered = self.filter.filter(
            matches
        )

        aggregated = self.aggregator.aggregate(
            filtered
        )

        skills = SkillFormatter.to_skill_names(
            aggregated
        )

        normalized = [
            self.normalizer.normalize(skill)
            for skill in skills
        ]

        return normalized

    def extract_with_confidence(
        self,
        text: str,
    ):
        scan_text = self._mask_non_skill_entities(
            text
        )

        return self.strategy.extract_with_confidence(
            scan_text
        )

    def _mask_non_skill_entities(
        self,
        text: str,
    ) -> str:

        if not text or self.ner_service is None:
            return text

        try:
            entities = self.ner_service.extract(
                text
            )
        except Exception as exc:
            logger.warning(
                "NER pre-filtering failed, falling back to "
                "unmasked text for skill matching: {}",
                exc,
            )
            return text

        if not entities:
            return text

        return self._apply_entity_mask(
            text,
            entities,
        )

    @classmethod
    def _apply_entity_mask(
        cls,
        text: str,
        entities: List[Dict],
    ) -> str:

        masked_count = 0

        characters = list(text)

        text_length = len(characters)

        for entity in entities:

            label = str(
                entity.get(
                    "label",
                    "",
                )
            ).upper()

            if label not in cls.NON_SKILL_LABELS:
                continue

            start = entity.get("start")
            end = entity.get("end")

            if start is None or end is None:
                continue

            start = int(start)
            end = int(end)

            if (
                start < 0
                or end <= start
                or end > text_length
            ):
                continue

            for index in range(start, end):

                if characters[index] != "\n":
                    characters[index] = " "

            masked_count += 1

        if masked_count:
            logger.debug(
                "Masked {} non-skill named entity span(s) before "
                "skill matching.",
                masked_count,
            )

        return "".join(characters)