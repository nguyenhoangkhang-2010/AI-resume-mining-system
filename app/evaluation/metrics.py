import math
from typing import Dict, Iterable, List, Sequence

import numpy as np


DEFAULT_RELEVANT_THRESHOLD = 2


def _relevant_ids(
    grades: Dict[str, int],
    threshold: int,
) -> set:
    return {
        candidate_id
        for candidate_id, grade in grades.items()
        if grade >= threshold
    }


def ndcg_at_k(
    ranked_ids: Sequence[str],
    grades: Dict[str, int],
    k: int,
) -> float:
    """
    Normalised discounted cumulative gain with exponential gain
    (2^grade - 1). Returns 0.0 when nothing relevant exists.
    """

    def dcg(values: Iterable[int]) -> float:
        return sum(
            (2 ** grade - 1) / math.log2(position + 2)
            for position, grade in enumerate(values)
        )

    gains = [grades.get(candidate_id, 0) for candidate_id in ranked_ids[:k]]

    ideal = sorted(grades.values(), reverse=True)[:k]

    ideal_dcg = dcg(ideal)

    if ideal_dcg == 0:
        return 0.0

    return dcg(gains) / ideal_dcg


def reciprocal_rank(
    ranked_ids: Sequence[str],
    grades: Dict[str, int],
    threshold: int = DEFAULT_RELEVANT_THRESHOLD,
) -> float:

    relevant = _relevant_ids(grades, threshold)

    for position, candidate_id in enumerate(ranked_ids, start=1):
        if candidate_id in relevant:
            return 1.0 / position

    return 0.0


def recall_at_k(
    ranked_ids: Sequence[str],
    grades: Dict[str, int],
    k: int,
    threshold: int = DEFAULT_RELEVANT_THRESHOLD,
) -> float:

    relevant = _relevant_ids(grades, threshold)

    if not relevant:
        return 0.0

    hits = sum(
        1 for candidate_id in ranked_ids[:k] if candidate_id in relevant
    )

    return hits / len(relevant)


def precision_at_k(
    ranked_ids: Sequence[str],
    grades: Dict[str, int],
    k: int,
    threshold: int = DEFAULT_RELEVANT_THRESHOLD,
) -> float:

    if k <= 0:
        return 0.0

    relevant = _relevant_ids(grades, threshold)

    hits = sum(
        1 for candidate_id in ranked_ids[:k] if candidate_id in relevant
    )

    return hits / k


def average_precision(
    ranked_ids: Sequence[str],
    grades: Dict[str, int],
    threshold: int = DEFAULT_RELEVANT_THRESHOLD,
) -> float:

    relevant = _relevant_ids(grades, threshold)

    if not relevant:
        return 0.0

    hits = 0
    total = 0.0

    for position, candidate_id in enumerate(ranked_ids, start=1):
        if candidate_id in relevant:
            hits += 1
            total += hits / position

    return total / len(relevant)


def bootstrap_mean_ci(
    values: Sequence[float],
    confidence: float = 0.95,
    n_resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """
    Mean and percentile bootstrap confidence interval, resampling
    queries (jobs) with replacement.
    """

    if not len(values):
        return 0.0, 0.0, 0.0

    data = np.asarray(values, dtype=float)

    rng = np.random.default_rng(seed)

    indices = rng.integers(0, len(data), size=(n_resamples, len(data)))

    means = data[indices].mean(axis=1)

    alpha = (1 - confidence) / 2

    low, high = np.quantile(means, [alpha, 1 - alpha])

    return float(data.mean()), float(low), float(high)


def paired_bootstrap_difference(
    values_a: Sequence[float],
    values_b: Sequence[float],
    confidence: float = 0.95,
    n_resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """
    Mean of (a - b) over the same queries with its bootstrap
    confidence interval. An interval that excludes 0 indicates a
    difference that is unlikely to come from query sampling alone.
    """

    if len(values_a) != len(values_b):
        raise ValueError("Paired samples must have the same length")

    differences: List[float] = [
        a - b for a, b in zip(values_a, values_b)
    ]

    return bootstrap_mean_ci(
        differences,
        confidence=confidence,
        n_resamples=n_resamples,
        seed=seed,
    )
