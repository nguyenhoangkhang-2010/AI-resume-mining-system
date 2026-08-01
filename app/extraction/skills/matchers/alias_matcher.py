from flashtext import KeywordProcessor
from loguru import logger
from app.extraction.skills.matchers.base_matcher import BaseMatcher


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

    def _match(self, text):
        matches = self.keyword_processor.extract_keywords(text)

        return set(matches)