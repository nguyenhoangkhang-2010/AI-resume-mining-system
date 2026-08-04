import json

from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule
)


class AliasNormalizationRule(
    NormalizationRule
):

    def __init__(
        self,
        path: str
    ):
        with open(
            path,
            encoding="utf-8"
        ) as file:

            self.aliases = json.load(file)


    def apply(
        self,
        skill: str
    ) -> str | None:

        return self.aliases.get(skill)