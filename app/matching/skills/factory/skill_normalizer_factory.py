from app.core.config.settings import settings

from app.infrastructure.repositories.json_skill_alias_repository import (
    JsonSkillAliasRepository,
)

from app.matching.skills.normalization.alias_rule import (
    AliasNormalizationRule,
)

from app.matching.skills.normalization.skill_normalizer import (
    SkillNormalizer,
)


def create_skill_normalizer():

    repository = JsonSkillAliasRepository(
        settings.skill_alias_path
    )


    return SkillNormalizer(
        rules=[
            AliasNormalizationRule(
                repository
            )
        ]
    )