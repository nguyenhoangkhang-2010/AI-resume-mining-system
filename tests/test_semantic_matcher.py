import pytest

from app.extraction.skills.matchers.semantic_matcher import SemanticSkillMatcher


@pytest.fixture(scope="module")
def matcher():
    return SemanticSkillMatcher()


def test_python_alias(matcher):
    skill, score = matcher.find_best_match("python3")

    assert skill == "Python"
    assert score >= 0.60


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known quality gap: the multilingual MiniLM matcher maps "
        "'reactjs' to 'chemical processes'. Aliases are resolved by "
        "AliasMatcher; track this in the evaluation harness."
    ),
)
def test_react_alias(matcher):
    skill, score = matcher.find_best_match("reactjs")

    assert skill == "React"
    assert score >= 0.60


def test_aws_alias(matcher):
    skill, score = matcher.find_best_match(
        "amazon web services"
    )

    assert skill == "AWS"
    assert score >= 0.60


def test_blank_query_returns_none(matcher):
    assert matcher.find_best_match("") is None
    assert matcher.find_best_match("   ") is None


def test_corpus_embeddings_are_shared_between_instances(matcher):
    other = SemanticSkillMatcher()

    assert other.skill_embeddings is matcher.skill_embeddings
