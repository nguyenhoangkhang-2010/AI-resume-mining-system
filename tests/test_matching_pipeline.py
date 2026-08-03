from app.matching.pipelines.matching_pipeline import (
    MatchingPipeline,
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