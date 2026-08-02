from flashtext import KeywordProcessor
from loguru import logger
from app.extraction.skills.matchers.base_matcher import BaseMatcher
from app.models.skill_match import SkillMatch
from app.extraction.skills.config.matching_config import MatchingConfig


class AliasMatcher(BaseMatcher):

    def __init__(self, repository):
        self.repository = repository

        self.keyword_processor = KeywordProcessor(
            case_sensitive=False
        )

        for alias, canonical in repository.get_alias_map().items():
            self.keyword_processor.add_keyword(
                alias,
                canonical
            )

    def match_with_confidence(self, text):
        matches = self.keyword_processor.extract_keywords(text)

        return [
            SkillMatch(
                skill=skill,
                confidence=MatchingConfig.ALIAS_CONFIDENCE,
                source="alias",
            )
            for skill in set(matches)
        ]