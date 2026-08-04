from app.matching.skills.normalization.trim_whitespace_rule import (
    TrimWhitespaceRule,
)


def test_trim_whitespace():

    rule = TrimWhitespaceRule()

    assert rule.apply(" Python ") == "Python"