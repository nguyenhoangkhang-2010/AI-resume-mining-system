from app.matching.skills.normalization.alias_rule import (
    AliasNormalizationRule,
)

from tests.fakes.fake_skill_alias_repository import (
    FakeSkillAliasRepository,
)


def test_python_alias():

    repository = FakeSkillAliasRepository(
        {
            "python3": "python"
        }
    )


    rule = AliasNormalizationRule(
        repository
    )


    result = rule.apply(
        "python3"
    )


    assert result == "python"