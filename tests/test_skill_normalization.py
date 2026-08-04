from app.matching.skills.normalization.alias_rule import (
    AliasNormalizationRule
)


def test_python_alias():

    rule = AliasNormalizationRule(
        "data/dictionaries/skill_aliases.json"
    )


    result = rule.apply(
        "python3"
    )


    assert result == "python"