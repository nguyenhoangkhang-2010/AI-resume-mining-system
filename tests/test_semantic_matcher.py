from app.extraction.skills.semantic_matcher import SemanticSkillMatcher


matcher = SemanticSkillMatcher()


def test_python_alias():
    skill, score = matcher.find_best_match("python3")

    assert skill == "Python"
    assert score >= 0.60


def test_react_alias():
    skill, score = matcher.find_best_match("reactjs")

    assert skill == "React"
    assert score >= 0.60


def test_aws_alias():
    skill, score = matcher.find_best_match(
        "amazon web services"
    )

    assert skill == "AWS"
    assert score >= 0.60


def test_unknown_skill():
    assert matcher.find_best_match("pizza") is None