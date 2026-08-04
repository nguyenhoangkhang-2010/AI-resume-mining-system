import re

from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class PunctuationNormalizationRule(
    NormalizationRule
):

    def apply(
        self,
        skill: str,
    ) -> str:

        return re.sub(
            r"^[^\w]+|[^\w]+$",
            "",
            skill,
        )