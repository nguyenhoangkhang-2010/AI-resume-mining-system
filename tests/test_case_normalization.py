from app.matching.skills.normalization.case_rule import (
    CaseNormalizationRule,
)


def test_case_normalization():

    rule = CaseNormalizationRule()

    assert rule.apply("PYTHON") == "python"
    assert rule.apply("FastAPI") == "fastapi"