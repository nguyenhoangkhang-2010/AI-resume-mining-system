from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.pipeline import SkillExtractionPipeline
from app.extraction.skills.factory.matcher_factory import MatcherFactory
from app.extraction.skills.formatters.skill_formatter import (
    SkillFormatter,
)
from app.extraction.skills.bootstrap import (
    build_skill_normalizer,
)

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

        self.normalizer = build_skill_normalizer()

        logger.info("SkillExtractor initialized.")
        
    def extract(self, text: str):
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []

        matches = self.pipeline.extract(text)

        skills = SkillFormatter.to_skill_names(
            matches
        )

        return [
            self.normalizer.normalize(skill)
            for skill in skills
        ]
        
    def extract_many(
        self,
        texts: list[str],
    ) -> list[list[str]]:

        return [
            self.extract(text)
            for text in texts
        ]
    # TODO:
    # Optimize using batch semantic embedding.