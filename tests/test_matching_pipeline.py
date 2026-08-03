from app.matching.pipelines.matching_pipeline import (
    MatchingPipeline,
)
from app.matching.strategies.hybrid_matching_strategy import (
    HybridMatchingStrategy,
)

from app.matching.filters.score_threshold_filter import (
    ScoreThresholdFilter,
)


def test_matching_pipeline():

    pipeline = MatchingPipeline()

    result = pipeline.process(
        candidate_id="candidate-1",
        job_id="job-1",
        skill_score=90,
        semantic_score=80,
    )

    assert result.overall_score == 86
    assert result.candidate_id == "candidate-1"
    assert result.job_id == "job-1"
    
def test_matching_pipeline_filters_low_score():

    pipeline = MatchingPipeline()

    result = pipeline.process(
        candidate_id="candidate-1",
        job_id="job-1",
        skill_score=20,
        semantic_score=20,
    )

    assert result is None
    
def test_pipeline_supports_dependency_injection():
    pipeline = MatchingPipeline(
        strategy=HybridMatchingStrategy(),
        score_filter=ScoreThresholdFilter(threshold=70),
    )

    assert pipeline.strategy is not None
    assert pipeline.filter.threshold == 70