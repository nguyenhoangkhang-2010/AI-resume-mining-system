from app.extraction.skills.matchers.alias_matcher import AliasMatcher
from app.extraction.skills.matchers.exact_matcher import ExactMatcher
from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher

from app.extraction.skills.registry.matcher_registry import MatcherRegistry
from app.extraction.skills.strategies.sequential_strategy import (
    SequentialStrategy,
)


class MatcherFactory:

    def __init__(self, repository):
        self.repository = repository

    def build_strategy(self):

        registry = MatcherRegistry()

        registry.register(
            ExactMatcher(self.repository)
        )

        registry.register(
            AliasMatcher(self.repository)
        )

        registry.register(
            SemanticSkillMatcher()
        )

        return SequentialStrategy(
            registry.get_matchers()
        )