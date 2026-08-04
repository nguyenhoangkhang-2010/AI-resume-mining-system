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

    def __init__(
        self, 
        strategy: MatchingStrategy
    ):
        self.strategy = strategy
        self.aggregator = ResultAggregator()
        self.filter = ConfidenceFilter()
        self.normalizer = build_skill_normalizer()

    def extract(self, text):

        logger.debug(
            "Starting skill extraction pipeline."
        )

        matches = self.strategy.extract(text)

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
        return self.strategy.extract_with_confidence(text)