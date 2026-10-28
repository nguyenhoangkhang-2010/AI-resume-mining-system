"""
Runs the offline evaluation and writes a markdown report.

    python -m scripts.run_evaluation --dataset data/evaluation/synthetic_v1 \
        --out docs/evaluation/synthetic_v1.md

Use --embedding hashing for a quick run without downloading the
sentence-transformer model (semantic rows are then not meaningful), and
--skip-extraction to skip the skill-extraction benchmark.
"""

import argparse
from datetime import date
from pathlib import Path

from app.evaluation.dataset import EvalDataset
from app.evaluation.extraction import (
    evaluate_skill_extraction,
    extraction_table,
    weakest_skills,
)
from app.evaluation.rankers import (
    HashingEmbedder,
    ServiceEmbedder,
    build_default_rankers,
)
from app.evaluation.runner import (
    evaluate_all,
    paired_difference_table,
    results_table,
)
from app.evaluation.synthetic import FAMILIES
from app.matching.skills.factory.skill_normalizer_factory import (
    create_skill_normalizer,
)


METRICS = ["ndcg@10", "ndcg@50", "mrr", "map", "recall@50", "precision@10"]

QRELS_DESCRIPTION = {
    "seniority_aware": (
        "Labels combine role family and seniority (0-3): same family and "
        "enough experience = 3, one year short = 2, otherwise 1; adjacent "
        "family with enough experience = 1."
    ),
    "family_only": (
        "Labels depend only on role family (0-2): same family = 2, adjacent "
        "family = 1. Seniority is ignored."
    ),
}


def skill_vocabulary() -> list[str]:
    return sorted(
        {
            skill
            for spec in FAMILIES.values()
            for skill in spec["core"] + spec["extra"]
        }
    )


def run_ranking(dataset, embedder, normalizer, lines):
    for name, qrels in dataset.qrels.items():
        rankers = build_default_rankers(embedder, normalizer)
        results = evaluate_all(rankers, dataset, qrels)

        lines += [
            f"### Labels: `{name}`",
            "",
            QRELS_DESCRIPTION.get(name, ""),
            "",
            "Mean over jobs with 95% bootstrap confidence interval.",
            "",
            results_table(results, METRICS),
            "",
            "Paired difference in nDCG@10 (hybrid minus other ranker, same jobs):",
            "",
            paired_difference_table(results, "hybrid", "ndcg@10"),
            "",
        ]


def run_extraction(dataset, lines):
    from app.extraction.skills.skill_extractor import SkillExtractor

    report = evaluate_skill_extraction(
        SkillExtractor(),
        dataset.extraction_documents,
        skill_vocabulary(),
    )

    lines += [
        "## Skill extraction",
        "",
        "Rule/semantic `SkillExtractor` on synthetic resume text. Only skills "
        "in the evaluated vocabulary are scored.",
        "",
        extraction_table(report),
        "",
        "Lowest per-skill recall (fraction of documents where the skill was "
        "found):",
        "",
        "| Skill | Recall |",
        "|---|---|",
        *[
            f"| {skill} | {recall:.2f} |"
            for skill, recall in weakest_skills(report)
        ],
        "",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/evaluation/synthetic_v1")
    parser.add_argument("--out", default="docs/evaluation/synthetic_v1.md")
    parser.add_argument(
        "--embedding", choices=["real", "hashing"], default="real"
    )
    parser.add_argument("--skip-extraction", action="store_true")
    args = parser.parse_args()

    dataset = EvalDataset.load(args.dataset)

    embedder = (
        ServiceEmbedder() if args.embedding == "real" else HashingEmbedder()
    )

    lines = [
        "# Offline evaluation on the synthetic dataset",
        "",
        f"Generated {date.today().isoformat()} by `scripts/run_evaluation.py` "
        f"(dataset seed {dataset.seed}, embedding: {args.embedding}).",
        "",
        f"- Jobs: {len(dataset.jobs)}",
        f"- Candidates: {len(dataset.candidates)}",
        "",
        "## Limitations",
        "",
        "- The data is synthetic. Labels come from latent attributes (role "
        "family, years of experience), and skill lists are generated with "
        "noise (missing skills, off-role skills, alias spellings, keyword "
        "stuffers). The numbers measure behaviour under that noise model, "
        "not real-world hiring accuracy.",
        "- The noise parameters were raised once after a first version made "
        "every ranker score ~1.0 on family-only labels; they were not tuned "
        "towards any ranker.",
        f"- Only {len(dataset.jobs)} jobs are used, so confidence intervals "
        "are wide; read differences together with the paired intervals.",
        "- The ranker named `hybrid` is the production scoring path "
        "(skill coverage + skills-only embedding + experience) without its "
        "minimum-score filter.",
        "",
        "## Ranking",
        "",
    ]

    run_ranking(dataset, embedder, create_skill_normalizer(), lines)

    if not args.skip_extraction and dataset.extraction_documents:
        run_extraction(dataset, lines)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Report written to {output}")


if __name__ == "__main__":
    main()
