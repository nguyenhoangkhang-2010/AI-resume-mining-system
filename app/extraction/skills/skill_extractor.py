from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.matchers.exact_matcher import ExactMatcher
from app.extraction.skills.matchers.alias_matcher import AliasMatcher
from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher
from app.extraction.skills.pipeline import SkillExtractionPipeline

from loguru import logger


class SkillExtractor:

    def __init__(self):

        repository = SkillRepository()

        self.pipeline = SkillExtractionPipeline(
            exact_matcher=ExactMatcher(repository),
            alias_matcher=AliasMatcher(repository),
            semantic_matcher=SemanticSkillMatcher(),
        )

        logger.info("SkillExtractor initialized.")
        
    def extract(self, text: str):
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []

        return self.pipeline.extract(text)