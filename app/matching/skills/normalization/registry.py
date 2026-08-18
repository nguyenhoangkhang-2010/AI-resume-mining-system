from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class NormalizationRuleRegistry:

    def __init__(
        self,
        rules: list[NormalizationRule],
    ):
        self.rules = rules

    def get_rules(
        self,
    ) -> list[NormalizationRule]:

        return self.rules