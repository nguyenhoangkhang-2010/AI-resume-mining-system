from loguru import logger

from app.extraction.skills.strategies.matching_strategy import (
    MatchingStrategy,
)


class SequentialStrategy(MatchingStrategy):

    def __init__(self, matchers):
        self.matchers = matchers

    def extract(self, text: str):

        logger.debug(
            "Running SequentialStrategy."
        )

        matches = []

        for matcher in self.matchers:

            result = matcher.match_with_confidence(
                text
            )

            if result:
                matches.extend(result)

        return matches