from loguru import logger
from app.extraction.skills.strategies.matching_strategy import (
    MatchingStrategy,
)


class SkillExtractionPipeline:

    def __init__(
        self, 
        strategy: MatchingStrategy
    ):
        self.strategy = strategy

    def extract(self, text):

        logger.debug(
            "Starting skill extraction pipeline."
        )

        return self.strategy.extract(text)
    
    def extract_with_confidence(
        self,
        text: str,
    ):
        return self.strategy.extract_with_confidence(text)