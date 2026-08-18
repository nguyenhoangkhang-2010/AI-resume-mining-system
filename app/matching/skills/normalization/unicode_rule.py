import unicodedata

from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class UnicodeNormalizationRule(
    NormalizationRule
):

    def apply(
        self,
        skill: str,
    ) -> str:

        return unicodedata.normalize(
            "NFKC",
            skill,
        )