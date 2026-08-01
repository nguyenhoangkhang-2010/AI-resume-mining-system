from flashtext import KeywordProcessor
from loguru import logger


class AliasMatcher:

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

    def match(self, text):
        if not text:
            logger.warning("Empty text provided.")
            return set()

        matches = self.keyword_processor.extract_keywords(text)

        return set(matches)