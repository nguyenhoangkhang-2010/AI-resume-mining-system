from loguru import logger
from app.extraction.skills.strategies.matching_strategy import (
    MatchingStrategy,
)
from app.extraction.skills.aggregation.result_aggregator import (
    ResultAggregator,
)


class SkillExtractionPipeline:

    def __init__(
        self, 
        strategy: MatchingStrategy
    ):
        self.strategy = strategy
        self.aggregator = ResultAggregator()

    def extract(self, text):

        logger.debug(
            "Starting skill extraction pipeline."
        )

        matches = self.strategy.extract(text)

        return self.aggregator.aggregate(
            matches
        )
    
    def extract_with_confidence(
        self,
        text: str,
    ):
        return self.strategy.extract_with_confidence(text)