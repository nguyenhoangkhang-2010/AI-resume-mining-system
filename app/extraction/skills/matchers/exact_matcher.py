from flashtext import KeywordProcessor
from loguru import logger


class ExactMatcher:

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

    def match(self, text):
        if not text:
            logger.warning("Empty text provided.")
            return set()

        matches = self.keyword_processor.extract_keywords(text)

        return set(matches)