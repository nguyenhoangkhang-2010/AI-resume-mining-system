from app.models.matching_weights import MatchingWeights
from app.matching.scoring.weighted_scorer import WeightedScorer


def test_custom_scoring_weights():

    weights = MatchingWeights(
        skill_weight=0.8,
        semantic_weight=0.2,
    )

    scorer = WeightedScorer(weights)

    score = scorer.calculate(
        skill_score=90,
        semantic_score=80,
    )

    assert score == 88.0