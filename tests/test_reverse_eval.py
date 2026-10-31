import pytest

from app.evaluation.dataset import EvalCandidate, EvalDataset, EvalJob
from app.evaluation.rankers import Ranker
from app.evaluation.reverse import (
    RandomRanker,
    evaluate_all_reverse,
    evaluate_reverse,
    jobs_for,
    score_matrix,
    transpose_qrels,
)


def job(job_id):
    return EvalJob(id=job_id, title=job_id, family="f", description="", required_skills=[])


def candidate(candidate_id):
    return EvalCandidate(id=candidate_id, title="", summary="", skills=[])


QRELS = {
    "j1": {"c1": 3, "c2": 0},
    "j2": {"c1": 0, "c2": 3},
    "j3": {"c1": 1, "c2": 0},
}


@pytest.fixture
def dataset():
    return EvalDataset(
        jobs=[job("j1"), job("j2"), job("j3")],
        candidates=[candidate("c1"), candidate("c2"), candidate("c3")],
        qrels={"labels": QRELS},
    )


class Oracle(Ranker):
    """Scores a pair by its true grade: the best possible ordering."""

    name = "oracle"

    def scores(self, job):
        return {c.id: float(QRELS[job.id].get(c.id, 0)) for c in self.dataset.candidates}


class Inverse(Oracle):
    name = "inverse"

    def scores(self, job):
        return {cid: -score for cid, score in super().scores(job).items()}


def test_labels_are_read_from_the_candidate_side():
    assert transpose_qrels(QRELS) == {
        "c1": {"j1": 3, "j2": 0, "j3": 1},
        "c2": {"j1": 0, "j2": 3, "j3": 0},
    }


def test_jobs_are_ordered_by_score_then_id():
    matrix = {"j2": {"c": 1.0}, "j1": {"c": 1.0}, "j3": {"c": 5.0}}

    assert jobs_for("c", matrix) == ["j3", "j1", "j2"]


def test_a_job_missing_a_score_goes_last():
    assert jobs_for("c", {"j1": {}, "j2": {"c": 0.1}}) == ["j2", "j1"]


def test_the_score_matrix_covers_every_job(dataset):
    ranker = Oracle()
    ranker.prepare(dataset)

    assert set(score_matrix(ranker, dataset)) == {"j1", "j2", "j3"}


def test_a_perfect_ranker_scores_one(dataset):
    ranker = Oracle()
    ranker.prepare(dataset)

    result = evaluate_reverse(ranker, dataset, QRELS)

    assert result.per_job["ndcg@3"] == [1.0, 1.0]
    assert result.per_job["mrr"] == [1.0, 1.0]


def test_the_worst_ordering_scores_lower(dataset):
    results = evaluate_all_reverse([Oracle(), Inverse()], dataset, QRELS)

    assert sum(results[0].per_job["ndcg@3"]) > sum(results[1].per_job["ndcg@3"])


def test_candidates_with_no_relevant_job_are_left_out(dataset):
    ranker = Oracle()
    ranker.prepare(dataset)

    # c3 appears in no label; c1 and c2 each have a job graded 3
    assert len(evaluate_reverse(ranker, dataset, QRELS).per_job["mrr"]) == 2


def test_the_random_ranker_is_reproducible_and_seed_dependent(dataset):
    first, second, other = RandomRanker(seed=3), RandomRanker(seed=3), RandomRanker(seed=4)

    for ranker in (first, second, other):
        ranker.prepare(dataset)

    one = dataset.jobs[0]

    assert first.scores(one) == second.scores(one)
    assert first.scores(one) != other.scores(one)


def test_the_oracle_beats_random(dataset):
    results = evaluate_all_reverse([Oracle(), RandomRanker(seed=1)], dataset, QRELS)

    assert sum(results[0].per_job["ndcg@3"]) >= sum(results[1].per_job["ndcg@3"])
