import re

from loguru import logger


class AliasMatcher:

    def __init__(self, repository):
        self.repository = repository
        self.alias_map = repository.get_alias_map()

    def _build_pattern(self, skill: str):
        escaped = re.escape(skill)
        escaped = escaped.replace(r"\ ", r"\s+")
        return rf"\b{escaped}\b"

    def match(self, text):
        if not text:
            logger.warning("Empty text provided.")
            return set()

        extracted = set()

        for alias, canonical in self.alias_map.items():
            pattern = self._build_pattern(alias)

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):
                extracted.add(canonical)

        return extracted