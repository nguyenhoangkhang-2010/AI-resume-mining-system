from app.matching.pipelines.matching_pipeline import MatchingPipeline


def test_matching_pipeline_success():

    pipeline = MatchingPipeline()

    result = pipeline.process(
        candidate_id="candidate-1",
        job_id="job-1",
        skill_score=90,
        semantic_score=85,
    )

    assert result is not None
    assert result.candidate_id == "candidate-1"
    assert result.job_id == "job-1"
    assert result.overall_score > 0
    assert result.confidence_score > 0
    assert result.explanation is not None


def test_matching_pipeline_reject():

    pipeline = MatchingPipeline()

    result = pipeline.process(
        candidate_id="candidate-1",
        job_id="job-1",
        skill_score=10,
        semantic_score=10,
    )

    assert result is None