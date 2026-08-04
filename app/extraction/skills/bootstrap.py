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
from app.matching.skills.normalization.registry import (
    NormalizationRuleRegistry,
)
from app.matching.skills.normalization.case_rule import (
    CaseNormalizationRule,
)
from app.matching.skills.normalization.trim_whitespace_rule import (
    TrimWhitespaceRule,
)


def build_skill_normalizer() -> SkillNormalizer:

    repository = JsonSkillAliasRepository(
        settings.skill_alias_path
    )

    registry = NormalizationRuleRegistry(
        rules=[
            TrimWhitespaceRule(),
            CaseNormalizationRule(),
            AliasNormalizationRule(repository),
        ]
    )

    return SkillNormalizer(
        registry.get_rules()
    )