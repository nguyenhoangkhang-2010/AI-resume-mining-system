from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.matchers.exact_matcher import ExactMatcher
from app.extraction.skills.matchers.alias_matcher import AliasMatcher
from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher

from loguru import logger


class SkillExtractor:

    def __init__(self):

        self.skill_repository = SkillRepository()

        self.exact_matcher = ExactMatcher(
            self.skill_repository
        )

        self.alias_matcher = AliasMatcher(
            self.skill_repository
        )

        self.semantic_matcher = SemanticSkillMatcher()

        logger.info("SkillExtractor initialized.")
        
    def extract(self, text: str):
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []
        
        logger.debug("Starting skill extraction process.")
        
        exact_skills = self.exact_matcher.match(text)
        
        alias_skills = self.alias_matcher.match(text)
        
        skills = exact_skills | alias_skills

        if not skills:
            semantic_skills = (
                self.semantic_matcher.match(text)
            )
            skills |= semantic_skills
        return sorted(skills)