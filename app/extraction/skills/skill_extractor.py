from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.matchers.exact_matcher import ExactMatcher
from app.extraction.skills.matchers.alias_matcher import AliasMatcher
from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher
from app.extraction.skills.pipeline import SkillExtractionPipeline
from app.extraction.skills.strategies.sequential_strategy import (
    SequentialStrategy,
)

from loguru import logger


class SkillExtractor:

    def __init__(self):

        repository = SkillRepository()

        self.exact_matcher = ExactMatcher(repository)

        self.alias_matcher = AliasMatcher(repository)

        self.semantic_matcher = SemanticSkillMatcher()
        
        strategy = SequentialStrategy(
            [
                self.exact_matcher,
                self.alias_matcher,
                self.semantic_matcher,
            ]
        )

        self.pipeline = SkillExtractionPipeline(
            strategy
        )

        logger.info("SkillExtractor initialized.")
        
    def extract(self, text: str):
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []

        return self.pipeline.extract(text)