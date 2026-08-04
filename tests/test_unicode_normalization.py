from app.matching.skills.normalization.unicode_rule import (
    UnicodeNormalizationRule,
)


def test_unicode_normalization():

    rule = UnicodeNormalizationRule()

    assert (
        rule.apply("Cafe\u0301")
        ==
        "Café"
    )