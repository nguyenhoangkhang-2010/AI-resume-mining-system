"""
Evaluation of job recommendation: given a candidate, rank the jobs.

The rankers and the relevance labels of the synthetic dataset are defined from
the recruiter's side (a job and the candidates for it). A ranker's score for a
(job, candidate) pair is the same whichever side asks, so the candidate-side
ranking is built from the same scores: for each candidate, the jobs ordered by
the score they get with that candidate. Labels are read the other way round.

Scores of different jobs have to be comparable for that ordering to mean
anything. Cosine, coverage and the hybrid score are; BM25 is not (its scale
depends on the query) and is therefore not evaluated here.
"""

import random
from typing import Dict, List, Sequence

from app.evaluation import metrics
from app.evaluation.dataset import EvalDataset, EvalJob
from app.evaluation.rankers import Ranker
from app.evaluation.runner import RankerResult

DEFAULT_CUTOFFS = (3, 5)


class RandomRanker(Ranker):
    """Orders at random (reproducibly): the floor any real ranker must beat."""

    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def scores(self, job: EvalJob) -> Dict[str, float]:
        return {
            candidate.id: random.Random(f"{self.seed}-{job.id}-{candidate.id}").random()
            for candidate in self.dataset.candidates
        }


def transpose_qrels(
    qrels: Dict[str, Dict[str, int]]
) -> Dict[str, Dict[str, int]]:
    """job -> candidate -> grade  into  candidate -> job -> grade."""

    result: Dict[str, Dict[str, int]] = {}

    for job_id, grades in qrels.items():
        for candidate_id, grade in grades.items():
            result.setdefault(candidate_id, {})[job_id] = grade

    return result


def score_matrix(ranker: Ranker, dataset: EvalDataset) -> Dict[str, Dict[str, float]]:
    """job id -> candidate id -> score (the ranker must have been prepared)."""

    return {job.id: ranker.scores(job) for job in dataset.jobs}


def jobs_for(
    candidate_id: str, matrix: Dict[str, Dict[str, float]]
) -> List[str]:
    """Job ids, best score first (ties by id, so the order is reproducible)."""

    return sorted(
        matrix,
        key=lambda job_id: (-matrix[job_id].get(candidate_id, float("-inf")), job_id),
    )


def evaluate_reverse(
    ranker: Ranker,
    dataset: EvalDataset,
    qrels: Dict[str, Dict[str, int]],
    cutoffs: Sequence[int] = DEFAULT_CUTOFFS,
    threshold: int = metrics.DEFAULT_RELEVANT_THRESHOLD,
) -> RankerResult:
    """
    Per-candidate metrics. A candidate for whom no job is relevant has
    nothing to find and is left out. The values in `per_job` are per
    candidate (the field name is shared with the recruiter-side runner).
    """

    matrix = score_matrix(ranker, dataset)
    by_candidate = transpose_qrels(qrels)
    per_candidate: Dict[str, List[float]] = {}

    def record(name: str, value: float) -> None:
        per_candidate.setdefault(name, []).append(value)

    for candidate in dataset.candidates:
        grades = by_candidate.get(candidate.id, {})

        if not any(grade >= threshold for grade in grades.values()):
            continue

        ranked = jobs_for(candidate.id, matrix)

        for k in cutoffs:
            record(f"ndcg@{k}", metrics.ndcg_at_k(ranked, grades, k))
            record(f"recall@{k}", metrics.recall_at_k(ranked, grades, k, threshold))

        record(
            f"precision@{cutoffs[0]}",
            metrics.precision_at_k(ranked, grades, cutoffs[0], threshold),
        )
        record("mrr", metrics.reciprocal_rank(ranked, grades, threshold))
        record("map", metrics.average_precision(ranked, grades, threshold))

    return RankerResult(name=ranker.name, per_job=per_candidate)


def evaluate_all_reverse(
    rankers: Sequence[Ranker],
    dataset: EvalDataset,
    qrels: Dict[str, Dict[str, int]],
    cutoffs: Sequence[int] = DEFAULT_CUTOFFS,
) -> List[RankerResult]:
    results = []

    for ranker in rankers:
        ranker.prepare(dataset)
        results.append(evaluate_reverse(ranker, dataset, qrels, cutoffs))

    return results
