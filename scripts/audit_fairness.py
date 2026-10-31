"""
Counterfactual fairness audit of the ranking (see app/evaluation/fairness.py).

    python -m scripts.audit_fairness --out docs/evaluation/fairness_results.md

For each change that should not matter (pronoun, name, CV language, career
break ...) the same candidates are ranked with the change applied one way to
half of them and the other way to the rest, and the selection rates and score
shifts of the two groups are compared. The production ranker (`hybrid`) is
audited, and with `--rerank-model` the same ranker followed by the reranking
stage.

The report holds aggregate numbers only.
"""

import argparse
from datetime import date
from pathlib import Path
from typing import List

from loguru import logger

from app.evaluation.fairness import COUNTERFACTUALS, AuditResult, audit, audit_table
from app.matching import embedding_text
from app.evaluation.rankers import (
    CachedEmbedder,
    HybridRanker,
    RerankedRanker,
    ServiceEmbedder,
)
from app.evaluation.synthetic import SyntheticDatasetGenerator
from app.matching.reranking.cross_encoder_reranker import (
    CachedPairScorer,
    CrossEncoderPairScorer,
)
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/evaluation/fairness_results.md")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=8)
    parser.add_argument(
        "--without-neutral-text",
        action="store_true",
        help="embed the text as written, with pronouns and names (the behaviour before profile-v2)",
    )
    parser.add_argument("--rerank-model", help="also audit the ranker followed by this reranker")
    parser.add_argument("--rerank-weight", type=float, default=0.5)
    parser.add_argument("--rerank-top-n", type=int, default=50)
    args = parser.parse_args()

    logger.remove()

    embedding_text.NEUTRALISE_TEXT = not args.without_neutral_text

    embedder = CachedEmbedder(ServiceEmbedder())
    normalizer = create_skill_normalizer()
    dataset = SyntheticDatasetGenerator(seed=args.seed).generate()

    rankers = [HybridRanker(embedder, normalizer, use_experience=True)]

    if args.rerank_model:
        rankers.append(
            RerankedRanker(
                HybridRanker(embedder, normalizer, use_experience=True),
                CachedPairScorer(CrossEncoderPairScorer(args.rerank_model)),
                normalizer,
                top_n=args.rerank_top_n,
                weight=args.rerank_weight,
                name=f"hybrid + rerank (weight {args.rerank_weight:g})",
            )
        )

    results: List[AuditResult] = []

    for ranker in rankers:
        for counterfactual in COUNTERFACTUALS:
            results.append(
                audit(
                    ranker,
                    dataset,
                    counterfactual,
                    top_k=args.top_k,
                    repeats=args.repeats,
                    seed=args.seed,
                )
            )
            print(f"{ranker.name}: {counterfactual.name} done", flush=True)

    lines = [
        "# Counterfactual fairness audit",
        "",
        f"Generated {date.today().isoformat()} by `scripts/audit_fairness.py`. "
        f"{len(dataset.jobs)} jobs, {len(dataset.candidates)} synthetic candidates "
        f"(seed {dataset.seed}); the top {args.top_k} per job are selected; "
        f"{args.repeats} random splits of the candidates into groups A and B. "
        + (
            "Text embedded as written (no neutralisation)."
            if args.without_neutral_text
            else "Text embedded after neutralising pronouns, titles and names."
        ),
        "",
        "## What was changed",
        "",
        *[f"- **{c.name}**: {c.description}" for c in COUNTERFACTUALS],
        "",
        "## Results",
        "",
        audit_table(results),
        "",
        "Selection ratio: selection rate of group A divided by that of group B; "
        "1.0 means no difference, and the groups are random halves of the same "
        "candidates, so any difference comes from the change. *Detectable* means "
        "the interval of the ratio excludes 1; *Below 4/5* means the ratio is "
        "outside 0.8 to 1.25. Score shift is in points of the 0-100 match score.",
        "",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
