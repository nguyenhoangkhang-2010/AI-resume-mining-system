import math

import pytest

from app.evaluation import metrics


GRADES = {"a": 3, "b": 2, "c": 1}


def test_ndcg_is_one_for_ideal_ranking():
    assert metrics.ndcg_at_k(["a", "b", "c", "x"], GRADES, 4) == pytest.approx(1.0)


def test_ndcg_penalises_wrong_order():
    ideal = metrics.ndcg_at_k(["a", "b", "c"], GRADES, 3)
    swapped = metrics.ndcg_at_k(["c", "b", "a"], GRADES, 3)

    assert swapped < ideal


def test_ndcg_matches_hand_computation():
    # gains: 2^3-1=7 at rank 1, 0 at rank 2, 2^2-1=3 at rank 3
    dcg = 7 / math.log2(2) + 3 / math.log2(4)
    ideal = 7 / math.log2(2) + 3 / math.log2(3) + 1 / math.log2(4)

    assert metrics.ndcg_at_k(["a", "x", "b"], GRADES, 3) == pytest.approx(dcg / ideal)


def test_ndcg_with_no_relevant_documents_is_zero():
    assert metrics.ndcg_at_k(["a"], {}, 5) == 0.0


def test_ndcg_respects_cutoff():
    assert metrics.ndcg_at_k(["x", "y", "a"], GRADES, 2) == 0.0


def test_reciprocal_rank_uses_first_relevant():
    assert metrics.reciprocal_rank(["x", "c", "b"], GRADES) == pytest.approx(1 / 3)
    assert metrics.reciprocal_rank(["x", "y"], GRADES) == 0.0


def test_recall_and_precision_at_k():
    ranked = ["a", "x", "b", "y"]

    # relevant (grade >= 2) = {a, b}
    assert metrics.recall_at_k(ranked, GRADES, 3) == 1.0
    assert metrics.recall_at_k(ranked, GRADES, 1) == 0.5
    assert metrics.precision_at_k(ranked, GRADES, 4) == 0.5
    assert metrics.precision_at_k(ranked, GRADES, 0) == 0.0


def test_recall_without_relevant_documents_is_zero():
    assert metrics.recall_at_k(["a"], {"a": 1}, 1) == 0.0


def test_average_precision():
    # hits at rank 1 and 3: (1/1 + 2/3) / 2 relevant
    assert metrics.average_precision(["a", "x", "b"], GRADES) == pytest.approx(
        (1 + 2 / 3) / 2
    )


def test_bootstrap_ci_contains_mean_and_is_deterministic():
    values = [0.2, 0.4, 0.6, 0.8, 1.0]

    mean, low, high = metrics.bootstrap_mean_ci(values, seed=1)

    assert mean == pytest.approx(0.6)
    assert low <= mean <= high
    assert metrics.bootstrap_mean_ci(values, seed=1) == (mean, low, high)


def test_bootstrap_ci_of_constant_values_is_degenerate():
    assert metrics.bootstrap_mean_ci([0.5] * 10) == (0.5, 0.5, 0.5)


def test_bootstrap_ci_of_empty_input():
    assert metrics.bootstrap_mean_ci([]) == (0.0, 0.0, 0.0)


def test_paired_difference_detects_consistent_gain():
    better = [0.9, 0.8, 0.85, 0.95, 0.9, 0.88]
    worse = [0.5, 0.4, 0.45, 0.55, 0.5, 0.48]

    mean, low, high = metrics.paired_bootstrap_difference(better, worse)

    assert mean > 0
    assert low > 0


def test_paired_difference_requires_equal_lengths():
    with pytest.raises(ValueError):
        metrics.paired_bootstrap_difference([1.0], [1.0, 2.0])
