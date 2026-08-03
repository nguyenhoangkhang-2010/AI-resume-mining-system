from app.matching.filters.score_threshold_filter import (
    ScoreThresholdFilter,
)
from app.models.matching_score import MatchingScore


def test_accept_matching_score():

    score = MatchingScore(
        candidate_id="c1",
        job_id="j1",
        overall_score=75,
        confidence_score=80,
    )

    assert ScoreThresholdFilter().accept(score)


def test_reject_matching_score():

    score = MatchingScore(
        candidate_id="c1",
        job_id="j1",
        overall_score=45,
        confidence_score=80,
    )

    assert not ScoreThresholdFilter().accept(score)