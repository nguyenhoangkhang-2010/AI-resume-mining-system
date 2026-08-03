from app.matching.ranking.ranking_scorer import RankingScorer
from app.matching.ranking.ranking_config import RankingConfig
import pytest


def test_calculate_without_penalty():

    scorer = RankingScorer()

    score = scorer.calculate(
        similarity_score=0.8,
        skill_gaps=[],
    )

    assert score == 0.8
    
def test_calculate_with_penalty():

    config = RankingConfig(
        penalty_per_missing_skill=0.1,
    )

    scorer = RankingScorer(config)

    score = scorer.calculate(
        similarity_score=0.8,
        skill_gaps=["SQL"],
    )

    assert score == pytest.approx(0.7)
    
def test_score_never_negative():

    config = RankingConfig(
        penalty_per_missing_skill=0.1,
    )

    scorer = RankingScorer(config)

    score = scorer.calculate(
        similarity_score=0.05,
        skill_gaps=[
            "A",
            "B",
        ],
    )

    assert score == 0.0