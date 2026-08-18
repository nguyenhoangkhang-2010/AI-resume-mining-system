from app.matching.scoring.weighted_scorer import (
    WeightedScorer,
)


def test_weighted_score():

    scorer = WeightedScorer()

    score = scorer.calculate(
        skill_score=90,
        semantic_score=80,
    )

    assert score == 86