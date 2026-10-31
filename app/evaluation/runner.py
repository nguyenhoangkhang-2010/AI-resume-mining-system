from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from app.evaluation import metrics
from app.evaluation.dataset import EvalDataset
from app.evaluation.rankers import Ranker


DEFAULT_CUTOFFS = (10, 50)


@dataclass
class RankerResult:
    name: str
    # metric name -> value per job, in dataset job order
    per_job: Dict[str, List[float]] = field(default_factory=dict)


def evaluate_ranker(
    ranker: Ranker,
    dataset: EvalDataset,
    qrels: Dict[str, Dict[str, int]],
    cutoffs: Sequence[int] = DEFAULT_CUTOFFS,
    threshold: int = metrics.DEFAULT_RELEVANT_THRESHOLD,
) -> RankerResult:

    per_job: Dict[str, List[float]] = {}

    def record(name: str, value: float) -> None:
        per_job.setdefault(name, []).append(value)

    for job in dataset.jobs:
        ranked = ranker.rank(job)
        grades = qrels.get(job.id, {})

        for k in cutoffs:
            record(f"ndcg@{k}", metrics.ndcg_at_k(ranked, grades, k))
            record(
                f"recall@{k}",
                metrics.recall_at_k(ranked, grades, k, threshold),
            )

        record(f"precision@{cutoffs[0]}", metrics.precision_at_k(
            ranked, grades, cutoffs[0], threshold
        ))
        record("mrr", metrics.reciprocal_rank(ranked, grades, threshold))
        record("map", metrics.average_precision(ranked, grades, threshold))

    return RankerResult(name=ranker.name, per_job=per_job)


def evaluate_all(
    rankers: Sequence[Ranker],
    dataset: EvalDataset,
    qrels: Dict[str, Dict[str, int]],
    cutoffs: Sequence[int] = DEFAULT_CUTOFFS,
) -> List[RankerResult]:

    results = []

    for ranker in rankers:
        ranker.prepare(dataset)
        results.append(evaluate_ranker(ranker, dataset, qrels, cutoffs))

    return results


def format_ci(values: Sequence[float], seed: int = 0) -> str:
    mean, low, high = metrics.bootstrap_mean_ci(values, seed=seed)

    return f"{mean:.3f} [{low:.3f}, {high:.3f}]"


def results_table(
    results: Sequence[RankerResult],
    metric_names: Sequence[str],
) -> str:

    header = "| Ranker | " + " | ".join(metric_names) + " |"
    divider = "|---|" + "---|" * len(metric_names)

    rows = [
        f"| {result.name} | "
        + " | ".join(format_ci(result.per_job[m]) for m in metric_names)
        + " |"
        for result in results
    ]

    return "\n".join([header, divider, *rows])


def paired_difference_table(
    results: Sequence[RankerResult],
    reference_name: str,
    metric_name: str,
) -> str:

    by_name = {result.name: result for result in results}

    reference = by_name[reference_name].per_job[metric_name]

    rows = ["| Compared with | Δ " + metric_name + " (95% CI) |", "|---|---|"]

    for result in results:
        if result.name == reference_name:
            continue

        mean, low, high = metrics.paired_bootstrap_difference(
            reference, result.per_job[metric_name]
        )

        verdict = (
            "significant" if low > 0 or high < 0 else "not significant"
        )

        rows.append(
            f"| {result.name} | {mean:+.3f} [{low:+.3f}, {high:+.3f}] ({verdict}) |"
        )

    return "\n".join(rows)
