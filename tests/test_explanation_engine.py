from app.matching.explanation.explanation_engine import (
    ExplanationEngine,
)


def test_generate_explanation():

    explanation = ExplanationEngine.generate(
        skill_score=90,
        semantic_score=80,
        overall_score=86,
    )

    assert "skill_score" in explanation
    assert "semantic_score" in explanation
    assert "overall_score" in explanation