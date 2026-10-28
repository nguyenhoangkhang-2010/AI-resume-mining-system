"""
Generates the synthetic evaluation dataset.

    python -m scripts.generate_eval_dataset --out data/evaluation/synthetic_v1

The output is fully determined by --seed, so the committed dataset can be
regenerated and compared byte for byte.
"""

import argparse

from app.evaluation.synthetic import SyntheticDatasetGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/evaluation/synthetic_v1")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--candidates", type=int, default=300)
    parser.add_argument("--jobs-per-family", type=int, default=5)
    parser.add_argument("--extraction-documents", type=int, default=100)
    args = parser.parse_args()

    dataset = SyntheticDatasetGenerator(
        seed=args.seed,
        n_candidates=args.candidates,
        jobs_per_family=args.jobs_per_family,
        n_extraction_documents=args.extraction_documents,
    ).generate()

    dataset.save(args.out)

    print(
        f"Wrote {len(dataset.jobs)} jobs, {len(dataset.candidates)} candidates "
        f"and {len(dataset.extraction_documents)} extraction documents "
        f"to {args.out} (seed={args.seed})"
    )


if __name__ == "__main__":
    main()
