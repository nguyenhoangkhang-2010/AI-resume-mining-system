from tests.fakes.fake_skill_alias_repository import (
    FakeSkillAliasRepository,
)

from app.matching.skills.normalization.alias_rule import (
    AliasNormalizationRule,
)


def test_alias_normalization():

    repository = FakeSkillAliasRepository(
        {
            "python3": "python"
        }
    )


    rule = AliasNormalizationRule(
        repository
    )


    assert rule.apply(
        "python3"
    ) == "python"