from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class TrimWhitespaceRule(
    NormalizationRule
):

    def apply(
        self,
        skill: str,
    ) -> str:

        return skill.strip()