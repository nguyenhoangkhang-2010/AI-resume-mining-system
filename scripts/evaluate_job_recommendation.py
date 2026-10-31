"""
Evaluates recommending jobs to candidates on the synthetic dataset.

    python -m scripts.evaluate_job_recommendation --out docs/evaluation/job_recommendation.md

For each candidate the jobs are ranked with the scores the recruiter-side
rankers give (see app/evaluation/reverse.py) and compared with the relevance
labels. Use --embedding hashing for a quick run without the embedding model
(semantic rows are then not meaningful).
"""

import argparse
from datetime import date
from pathlib import Path

from app.evaluation.dataset import EvalDataset
from app.evaluation.rankers import (
    CachedEmbedder,
    HashingEmbedder,
    HybridRanker,
    ProfileSemanticRanker,
    ServiceEmbedder,
    SkillOverlapRanker,
    TfidfRanker,
)
from app.evaluation.reverse import RandomRanker, evaluate_all_reverse
from app.evaluation.runner import paired_difference_table, results_table
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)

METRICS = ["ndcg@3", "ndcg@5", "mrr", "map", "recall@5", "precision@3"]

QRELS_DESCRIPTION = {
    "seniority_aware": (
        "Labels combine role family and seniority (0-3), as on the recruiter "
        "side: a job is graded 3 when it is in the candidate's family and the "
        "candidate has enough experience for it."
    ),
    "family_only": "Labels depend only on role family (0-2); seniority is ignored.",
}


def build_rankers(embedder, normalizer):
    embedder = CachedEmbedder(embedder)

    return [
        RandomRanker(),
        TfidfRanker(),
        SkillOverlapRanker(normalizer),
        ProfileSemanticRanker(embedder, normalizer, pooled=False),
        HybridRanker(embedder, normalizer, use_experience=False),
        HybridRanker(embedder, normalizer, use_experience=True),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/evaluation/synthetic_v1")
    parser.add_argument("--out", default="docs/evaluation/job_recommendation.md")
    parser.add_argument("--embedding", choices=["real", "hashing"], default="real")
    args = parser.parse_args()

    dataset = EvalDataset.load(args.dataset)
    embedder = ServiceEmbedder() if args.embedding == "real" else HashingEmbedder()
    normalizer = create_skill_normalizer()

    lines = [
        "# Job recommendation on the synthetic dataset",
        "",
        f"Generated {date.today().isoformat()} by "
        f"`scripts/evaluate_job_recommendation.py` (dataset seed {dataset.seed}, "
        f"embedding: {args.embedding}).",
        "",
        f"- Candidates: {len(dataset.candidates)} (each ranks {len(dataset.jobs)} jobs)",
        "",
        "## Limitations",
        "",
        "- The data is synthetic; labels come from latent attributes (role "
        "family, years of experience), so the numbers measure behaviour under "
        "that noise model, not real hiring.",
        f"- Each candidate chooses among only {len(dataset.jobs)} jobs, so "
        "the metrics are computed at small cutoffs; the `random` row shows what "
        "ordering the jobs at random scores. Candidates with no relevant job "
        "are left out.",
        "- BM25 is not evaluated: its scores are not comparable between jobs.",
        "- `hybrid` is the production scoring path. `hybrid_no_experience` "
        "drops the experience component.",
        "",
        "## Ranking jobs for a candidate",
        "",
    ]

    for name, qrels in dataset.qrels.items():
        results = evaluate_all_reverse(build_rankers(embedder, normalizer), dataset, qrels)
        counted = len(results[0].per_job["mrr"])

        lines += [
            f"### Labels: `{name}`",
            "",
            QRELS_DESCRIPTION.get(name, ""),
            "",
            f"Mean over {counted} candidates with at least one relevant job, "
            "with 95% bootstrap confidence intervals.",
            "",
            results_table(results, METRICS),
            "",
            "Paired difference in nDCG@3 (hybrid minus other ranker, same candidates):",
            "",
            paired_difference_table(results, "hybrid", "ndcg@3"),
            "",
        ]

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Report written to {output}")


if __name__ == "__main__":
    main()
