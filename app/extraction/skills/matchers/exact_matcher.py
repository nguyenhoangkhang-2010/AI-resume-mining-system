from flashtext import KeywordProcessor
from loguru import logger
from app.extraction.skills.matchers.base_matcher import BaseMatcher
from app.models.skill_match import SkillMatch
from app.extraction.skills.config.matching_config import MatchingConfig


class ExactMatcher(BaseMatcher):

    def __init__(self, repository):
        self.repository = repository

        self.keyword_processor = KeywordProcessor(
            case_sensitive=False
        )

        for skill in repository.get_all_skills():
            self.keyword_processor.add_keyword(
                skill,
                skill
            )

    def match_with_confidence(self, text: str,):
        matches = self.keyword_processor.extract_keywords(text)

        return [
            SkillMatch(
                skill=skill,
                confidence=MatchingConfig.EXACT_CONFIDENCE,
                source="exact",
            )
            for skill in set(matches)
        ]