from app.extraction.skills.matchers.exact_matcher import ExactMatcher
from app.extraction.skills.matchers.alias_matcher import AliasMatcher
from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher

from loguru import logger


class SkillExtractionPipeline:

    def __init__(
        self,
        exact_matcher: ExactMatcher,
        alias_matcher: AliasMatcher,
        semantic_matcher: SemanticSkillMatcher,
    ):
        self.exact_matcher = exact_matcher
        self.alias_matcher = alias_matcher
        self.semantic_matcher = semantic_matcher

    def extract(self, text):
        logger.debug("Starting skill extraction pipeline.")

        exact_skills = self.exact_matcher.match(text)

        alias_skills = self.alias_matcher.match(text)

        skills = exact_skills | alias_skills

        if not skills:
            logger.debug(
                "No exact or alias matches found. Falling back to semantic matcher."
            )

            semantic_skills = self.semantic_matcher.match(text)

            skills |= semantic_skills

        logger.debug(
            f"Pipeline extracted {len(skills)} skills."
        )

        return sorted(skills)