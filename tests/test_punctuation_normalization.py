from app.matching.skills.normalization.punctuation_rule import (
    PunctuationNormalizationRule,
)


def test_remove_trailing_punctuation():

    rule = PunctuationNormalizationRule()

    assert rule.apply("Python,") == "Python"
    assert rule.apply("(Python)") == "Python"
    assert rule.apply("Python.") == "Python"