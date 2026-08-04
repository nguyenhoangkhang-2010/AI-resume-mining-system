from app.core.config.settings import settings

from app.repositories.skill_alias_repository import (
    JsonSkillAliasRepository,
)

from app.matching.skills.normalization.alias_rule import (
    AliasNormalizationRule,
)

from app.matching.skills.normalization.skill_normalizer import (
    SkillNormalizer,
)


def build_skill_normalizer() -> SkillNormalizer:

    repository = JsonSkillAliasRepository(
        settings.skill_alias_path
    )

    return SkillNormalizer(
        rules=[
            AliasNormalizationRule(repository)
        ]
    )