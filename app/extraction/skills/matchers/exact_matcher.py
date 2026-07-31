import re

from loguru import logger


class ExactMatcher:

    def __init__(self, repository):
        self.repository = repository
        self.skills = repository.get_all_skills()

    def _build_pattern(self, skill: str):
        escaped = re.escape(skill)
        escaped = escaped.replace(r"\ ", r"\s+")
        return rf"\b{escaped}\b"

    def match(self, text):
        if not text:
            logger.warning("Empty text provided.")
            return set()

        extracted = set()

        for skill in self.skills:
            pattern = self._build_pattern(skill)

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):
                extracted.add(skill)

        return extracted