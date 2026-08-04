from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule
)


class NormalizerRegistry:

    def __init__(
        self,
        rules: list[NormalizationRule]
    ):
        self.rules = rules


    def normalize(
        self,
        skill: str
    ) -> str:

        normalized = skill.lower().strip()


        for rule in self.rules:

            result = rule.apply(
                normalized
            )

            if result:
                return result


        return normalized