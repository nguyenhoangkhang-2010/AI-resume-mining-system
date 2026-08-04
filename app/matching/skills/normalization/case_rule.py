from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class CaseNormalizationRule(
    NormalizationRule
):

    def apply(
        self,
        skill: str,
    ) -> str:

        return skill.lower()