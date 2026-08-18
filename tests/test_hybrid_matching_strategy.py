from app.matching.strategies.hybrid_matching_strategy import (
    HybridMatchingStrategy,
)


def test_hybrid_strategy():

    strategy = HybridMatchingStrategy()

    result = strategy.match(
        candidate_id="c1",
        job_id="j1",
        skill_score=90,
        semantic_score=80,
    )

    assert result.overall_score == 86.0
    assert result.confidence_score == 85.0