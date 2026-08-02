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


class SkillExtractionPipeline:

    def __init__(
        self, 
        strategy: MatchingStrategy
    ):
        self.strategy = strategy
        self.aggregator = ResultAggregator()
        self.filter = ConfidenceFilter()

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

        return aggregated
    
    def extract_with_confidence(
        self,
        text: str,
    ):
        return self.strategy.extract_with_confidence(text)