from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class SkillNormalizer:

    def __init__(
        self,
        rules: list[NormalizationRule]
    ):
        self.rules = rules


    def normalize(
        self,
        skill: str
    ) -> str:

        normalized = skill

        for rule in self.rules:
            normalized = rule.apply(
                normalized
            )

        return normalized