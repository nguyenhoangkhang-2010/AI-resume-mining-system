from types import SimpleNamespace

import pytest

from app.matching.ranking.ranking_pipeline import RankingPipeline
from app.matching.reranking.cross_encoder_reranker import (
    CachedPairScorer,
    CrossEncoderReranker,
    fuse_scores,
    scale_to_percent,
)
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.schemas.ranked_candidate_schema import ScoreBreakdown


class KeywordScorer:
    """Relevance = how many times the job's first word occurs in the profile text."""

    def __init__(self):
        self.calls = []

    def score(self, pairs):
        self.calls.append(list(pairs))

        return [float(candidate.count("python")) for _, candidate in pairs]


class BrokenScorer:
    def score(self, pairs):
        raise RuntimeError("model unavailable")


def item(score, name):
    return SimpleNamespace(
        similarity_score=score,
        name=name,
        score_breakdown=ScoreBreakdown(),
    )


def reranker(scorer, **options):
    return CrossEncoderReranker(
        scorer,
        candidate_text=lambda candidate: candidate,
        job_text=lambda job: "job",
        **options,
    )


def run(rr, items, texts):
    return rr.rerank(None, items, {id(i): t for i, t in zip(items, texts)})


def test_scaling_maps_the_window_to_zero_and_one_hundred():
    assert scale_to_percent([2.0, 4.0, 3.0]) == [0.0, 100.0, 50.0]
    assert scale_to_percent([5.0, 5.0]) == [50.0, 50.0]
    assert scale_to_percent([]) == []


def test_weight_zero_keeps_the_first_stage_and_one_uses_only_the_cross_encoder():
    first = [90.0, 60.0]
    ce = [0.0, 10.0]

    assert fuse_scores(first, ce, 0.0) == first
    assert fuse_scores(first, ce, 1.0) == [0.0, 100.0]
    assert fuse_scores(first, ce, 0.5) == [45.0, 80.0]


def test_bad_arguments_are_refused():
    with pytest.raises(ValueError):
        fuse_scores([1.0], [1.0, 2.0], 0.5)

    with pytest.raises(ValueError):
        fuse_scores([1.0], [1.0], 1.5)

    with pytest.raises(ValueError):
        CrossEncoderReranker(KeywordScorer(), top_n=0)


def test_the_cross_encoder_can_move_a_candidate_up():
    items = [item(80.0, "a"), item(70.0, "b"), item(60.0, "c")]
    texts = ["java", "python python", "python"]

    ordered = run(reranker(KeywordScorer(), weight=1.0), items, texts)

    assert [i.name for i in ordered] == ["b", "c", "a"]
    assert ordered[0].similarity_score == 100.0
    assert ordered[0].score_breakdown.rerank_score == 100.0


def test_the_blend_keeps_part_of_the_first_stage():
    items = [item(90.0, "a"), item(10.0, "b")]
    texts = ["java", "python"]

    ordered = run(reranker(KeywordScorer(), weight=0.3), items, texts)

    # 0.7*90 + 0 = 63 against 0.7*10 + 30 = 37
    assert [i.name for i in ordered] == ["a", "b"]


def test_candidates_below_the_window_stay_below_it_in_their_order():
    items = [item(80.0, "a"), item(70.0, "b"), item(60.0, "c"), item(50.0, "d")]
    scorer = KeywordScorer()

    ordered = run(reranker(scorer, top_n=2, weight=1.0), items, ["java", "python", "x", "y"])

    assert [i.name for i in ordered] == ["b", "a", "c", "d"]
    assert len(scorer.calls[0]) == 2
    assert items[2].score_breakdown.rerank_score is None


def test_a_failing_model_leaves_the_ranking_as_it_was():
    items = [item(80.0, "a"), item(70.0, "b")]

    ordered = run(reranker(BrokenScorer()), items, ["x", "y"])

    assert [i.name for i in ordered] == ["a", "b"]
    assert items[0].similarity_score == 80.0


def test_one_candidate_is_not_worth_a_model_run():
    scorer = KeywordScorer()

    run(reranker(scorer), [item(80.0, "a")], ["x"])

    assert scorer.calls == []


def test_the_cache_runs_each_pair_once():
    inner = KeywordScorer()
    cached = CachedPairScorer(inner)

    cached.score([("j", "python"), ("j", "java")])
    values = cached.score([("j", "python"), ("j", "go")])

    assert values == [1.0, 0.0]
    assert [len(call) for call in inner.calls] == [2, 1]


def test_the_ranking_pipeline_applies_the_reranker_to_hybrid_results():
    class Scorer:
        def score(self, job, candidate, semantic_score):
            return SimpleNamespace(
                overall_score=80.0 if candidate.resume_id == "r1" else 70.0,
                skill_score=50.0,
                semantic_score=semantic_score,
                experience_score=None,
                confidence_score=50.0,
                matched_skills=[],
                missing_skills=[],
                explanation={},
            )

    def candidate(resume_id, faiss_id, skill):
        return CandidateModel(resume_id=resume_id, faiss_id=faiss_id, skills=[skill], summary=skill)

    class Reranker:
        def rerank(self, job, ranked, candidates):
            assert all(id(r) in candidates for r in ranked)

            return list(reversed(ranked))

    pipeline = RankingPipeline(candidate_scorer=Scorer(), reranker=Reranker())
    job = JobModel(title="t", description="d", raw_text="d", required_skills=["python"])

    result = pipeline.process(
        job,
        [candidate("r1", 1, "python"), candidate("r2", 2, "java")],
        {1: 0.9, 2: 0.8},
    )

    assert [r.candidate_profile.skills for r in result.results] == [["java"], ["python"]]


def test_without_a_reranker_the_pipeline_is_unchanged():
    assert RankingPipeline().reranker is None
