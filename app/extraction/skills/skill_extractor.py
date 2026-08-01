from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.matchers.exact_matcher import ExactMatcher
from app.extraction.skills.matchers.alias_matcher import AliasMatcher
from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher
from app.extraction.skills.pipeline import SkillExtractionPipeline
from app.extraction.skills.strategies.sequential_strategy import (
    SequentialStrategy,
)
from app.extraction.skills.registry.matcher_registry import MatcherRegistry

from loguru import logger


class SkillExtractor:

    def __init__(self):

        repository = SkillRepository()

        self.exact_matcher = ExactMatcher(repository)

        self.alias_matcher = AliasMatcher(repository)

        self.semantic_matcher = SemanticSkillMatcher()
        
        self.registry = MatcherRegistry()
        
        self.registry.register(self.exact_matcher)
        self.registry.register(self.alias_matcher)
        self.registry.register(self.semantic_matcher)
        
        strategy = SequentialStrategy(
            self.registry.get_matchers()
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