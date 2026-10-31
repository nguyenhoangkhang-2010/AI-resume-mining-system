"""
Measures whether the cross-encoder reranking stage improves the ranking.

    python -m scripts.evaluate_reranking --out docs/evaluation/reranking_results.md

The blend weight is chosen on a development dataset (seed 42, the one used by
`run_evaluation`) and the chosen setting is then reported on a fresh test
dataset (another seed, more jobs) that played no part in the choice. Labels
come from the latent role family and years of experience of the synthetic
candidates, never from the text a reranker reads.

The report holds aggregate numbers only.
"""

import argparse
from datetime import date
from pathlib import Path
from typing import List, Sequence

from loguru import logger

from app.evaluation.dataset import EvalDataset
from app.evaluation.rankers import (
    CachedEmbedder,
    HybridRanker,
    RerankedRanker,
    ServiceEmbedder,
)
from app.evaluation.runner import (
    RankerResult,
    evaluate_all,
    paired_difference_table,
    results_table,
)
from app.evaluation.synthetic import SyntheticDatasetGenerator
from app.matching.reranking.cross_encoder_reranker import (
    CachedPairScorer,
    CrossEncoderPairScorer,
)
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)

METRICS = ["ndcg@10", "ndcg@50", "mrr", "map", "precision@10"]
WEIGHTS = (0.25, 0.5, 0.75, 1.0)
LABEL_SETS = ("seniority_aware", "family_only")


def model_label(model: str) -> str:
    """The model's hub name, also when `model` is a path into a local hub cache."""

    for part in Path(model).parts:
        if part.startswith("models--"):
            return part[len("models--"):].replace("--", "/")

    return model


def rankers_for(embedder, normalizer, pair_scorer, top_n: int, weights: Sequence[float]):
    base = HybridRanker(embedder, normalizer, use_experience=True)

    return [
        base,
        *[
            RerankedRanker(
                HybridRanker(embedder, normalizer, use_experience=True),
                pair_scorer,
                normalizer,
                top_n=top_n,
                weight=weight,
                name=f"hybrid + rerank, weight {weight:g}",
            )
            for weight in weights
        ],
    ]


def section(title: str, dataset: EvalDataset, rankers, top_n: int) -> List[str]:
    lines = [
        f"## {title}",
        "",
        f"{len(dataset.jobs)} jobs, {len(dataset.candidates)} candidates "
        f"(seed {dataset.seed}); the top {top_n} of the first stage are reranked.",
        "",
    ]

    for label_set in LABEL_SETS:
        results: List[RankerResult] = evaluate_all(
            rankers, dataset, dataset.qrels[label_set]
        )

        lines += [
            f"### Labels: `{label_set}`",
            "",
            "Mean over jobs with 95% bootstrap interval.",
            "",
            results_table(results, METRICS),
            "",
            "Paired difference in nDCG@10, `hybrid` minus the other ranker (same jobs; positive means hybrid is better):",
            "",
            paired_difference_table(results, "hybrid", "ndcg@10"),
            "",
        ]

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/evaluation/reranking_results.md")
    parser.add_argument(
        "--model",
        default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        help="reranker model name or local path",
    )
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--dev-seed", type=int, default=42)
    parser.add_argument("--test-seed", type=int, default=7)
    parser.add_argument("--test-jobs-per-family", type=int, default=10)
    args = parser.parse_args()

    logger.remove()

    embedder = CachedEmbedder(ServiceEmbedder())
    normalizer = create_skill_normalizer()
    pair_scorer = CachedPairScorer(CrossEncoderPairScorer(args.model))

    dev = SyntheticDatasetGenerator(seed=args.dev_seed).generate()
    test = SyntheticDatasetGenerator(
        seed=args.test_seed, jobs_per_family=args.test_jobs_per_family
    ).generate()

    lines = [
        "# Does cross-encoder reranking help?",
        "",
        f"Generated {date.today().isoformat()} by `scripts/evaluate_reranking.py`. "
        f"Reranker: `{model_label(args.model)}`.",
        "",
        "Synthetic data: labels come from the latent role family and years of "
        "experience, so the numbers show behaviour under that noise model, not "
        "hiring accuracy.",
        "",
    ]

    lines += section(
        "Development dataset (used to choose the blend weight)",
        dev,
        rankers_for(embedder, normalizer, pair_scorer, args.top_n, WEIGHTS),
        args.top_n,
    )
    print("dev done", flush=True)

    lines += section(
        "Test dataset (not used to choose anything)",
        test,
        rankers_for(embedder, normalizer, pair_scorer, args.top_n, WEIGHTS),
        args.top_n,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
