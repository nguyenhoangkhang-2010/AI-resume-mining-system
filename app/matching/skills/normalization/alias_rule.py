from app.repositories.skill_alias_repository import (
    SkillAliasRepository,
)

from app.matching.skills.normalization.normalization_rule import (
    NormalizationRule,
)


class AliasNormalizationRule(
    NormalizationRule
):

    def __init__(
        self,
        repository: SkillAliasRepository
    ):
        self.repository = repository


    def apply(
        self,
        skill: str
    ) -> str:

        alias = self.repository.get_alias(skill)

        if alias:
            return alias

        return skill