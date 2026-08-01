from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.pipeline import SkillExtractionPipeline
from app.extraction.skills.factory.matcher_factory import MatcherFactory

from loguru import logger


class SkillExtractor:

    def __init__(self):

        repository = SkillRepository()

        factory = MatcherFactory(
            repository
        )

        strategy = factory.build_strategy()

        self.pipeline = SkillExtractionPipeline(
            strategy
        )

        logger.info("SkillExtractor initialized.")
        
    def extract(self, text: str):
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []

        return self.pipeline.extract(text)