from flashtext import KeywordProcessor
from loguru import logger
from app.extraction.skills.matchers.base_matcher import BaseMatcher


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

    def _match(self, text):
        matches = self.keyword_processor.extract_keywords(text)

        return set(matches)