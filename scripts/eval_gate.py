"""
Quality gate for CI: fails when the system measurably gets worse.

    python -m scripts.eval_gate                 # compare with the baseline
    python -m scripts.eval_gate --update        # accept the current numbers

Unit tests say the code does what it was written to do; they do not say the
ranking or the section detection stay as good as they were. This runs the
same evaluations the reports are made from, on small fixed synthetic sets, and
compares a handful of headline numbers with `docs/evaluation/gate_baseline.json`:

- ranking: nDCG@10 and MRR of the production scorer on both label sets;
- section detection: line accuracy on the synthetic English/Vietnamese CVs and
  on the French, Spanish, German, Portuguese and Russian CVs (no language model);
- fairness: the score shift caused by a pronoun and by a name must stay at zero.

A number may fall by the tolerance (0.02 by default; the sets are small, so
smaller moves are noise) before the gate fails. Numbers that improve pass and
are reported, so the baseline can be raised with `--update` in the same commit.
Everything is deterministic (fixed seeds); the language model is not used.
"""

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List

from loguru import logger

BASELINE = Path("docs/evaluation/gate_baseline.json")
DEFAULT_TOLERANCE = 0.02

# Absolute limit for the fairness checks: points on the 0-100 match score.
MAX_SHIFT = 0.05


@dataclass
class Check:
    name: str
    value: float
    baseline: float
    tolerance: float

    @property
    def passed(self) -> bool:
        return self.value >= self.baseline - self.tolerance


def ranking_metrics() -> Dict[str, float]:
    from app.evaluation.rankers import CachedEmbedder, HybridRanker, ServiceEmbedder
    from app.evaluation.runner import evaluate_all
    from app.evaluation.synthetic import SyntheticDatasetGenerator
    from app.matching.skills.factory.skill_normalizer_factory import (
        create_skill_normalizer,
    )

    dataset = SyntheticDatasetGenerator(seed=42).generate()
    embedder = CachedEmbedder(ServiceEmbedder())
    normalizer = create_skill_normalizer()
    values: Dict[str, float] = {}

    for label_set in ("seniority_aware", "family_only"):
        result = evaluate_all(
            [HybridRanker(embedder, normalizer, use_experience=True)],
            dataset,
            dataset.qrels[label_set],
        )[0]

        for metric in ("ndcg@10", "mrr"):
            scores = result.per_job[metric]
            values[f"ranking.{label_set}.{metric}"] = sum(scores) / len(scores)

    return values


def section_metrics() -> Dict[str, float]:
    from app.evaluation.cv_corpus import CVCorpusBuilder
    from app.evaluation.cv_languages import build_language_corpus
    from app.evaluation.section_eval import aggregate, score_document
    from app.extraction.section.heading_classifier import HeadingClassifier
    from app.extraction.section.section_detector import SectionDetector
    from app.extraction.section.section_semantic_classifier import (
        SectionSemanticClassifier,
    )
    from app.resume_processing.pipelines.resume_pipeline import ResumePipeline
    from scripts.evaluate_sections import CountingNoLLM

    detector = SectionDetector(
        SectionSemanticClassifier(),
        CountingNoLLM(),  # type: ignore[arg-type]
        heading_classifier=HeadingClassifier(),
    )
    pipeline = ResumePipeline(detector, extraction_engine=None)  # type: ignore[arg-type]

    def accuracy(documents) -> float:
        results = [
            score_document(d, pipeline.detect_sections(d.path)) for d in documents
        ]

        return aggregate(results)["all"].f1

    with tempfile.TemporaryDirectory() as directory:
        english_vietnamese = CVCorpusBuilder(seed=42, per_variant=1).build(
            Path(directory) / "base"
        )
        other_languages = build_language_corpus(Path(directory) / "languages")

        return {
            "sections.english_vietnamese.line_accuracy": accuracy(english_vietnamese),
            "sections.other_languages.line_accuracy": accuracy(other_languages),
        }


def fairness_shifts() -> Dict[str, float]:
    from app.evaluation.fairness import find, score_shift
    from app.evaluation.rankers import CachedEmbedder, HybridRanker, ServiceEmbedder
    from app.evaluation.synthetic import SyntheticDatasetGenerator
    from app.matching.skills.factory.skill_normalizer_factory import (
        create_skill_normalizer,
    )

    dataset = SyntheticDatasetGenerator(seed=42, n_candidates=120).generate()
    ranker = HybridRanker(CachedEmbedder(ServiceEmbedder()), create_skill_normalizer())

    shifts = {}

    for name in ("pronoun", "name, Vietnamese", "name, Arabic", "career break"):
        counterfactual = find(name)
        assert counterfactual is not None
        mean, _, _, _ = score_shift(ranker, dataset, counterfactual)
        shifts[f"fairness.shift.{name}"] = abs(mean)

    return shifts


MEASURES: List[Callable[[], Dict[str, float]]] = [ranking_metrics, section_metrics]


def compare(measured: Dict[str, float], baseline: Dict[str, float], tolerance: float) -> List[Check]:
    checks = []

    for name, value in sorted(measured.items()):
        if name not in baseline:
            continue

        checks.append(Check(name, value, baseline[name], tolerance))

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--update", action="store_true", help="write the measured numbers as the new baseline")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args()

    logger.remove()

    measured: Dict[str, float] = {}

    for measure in MEASURES:
        measured.update(measure())

    shifts = fairness_shifts()
    path = Path(args.baseline)

    if args.update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "generated": date.today().isoformat(),
                    "tolerance": args.tolerance,
                    "metrics": {k: round(v, 4) for k, v in sorted(measured.items())},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Baseline written to {path}")
        return 0

    stored = json.loads(path.read_text(encoding="utf-8"))
    tolerance = float(stored.get("tolerance", args.tolerance))
    checks = compare(measured, stored["metrics"], tolerance)
    missing = sorted(set(stored["metrics"]) - set(measured))

    print(f"{'metric':<52}{'baseline':>10}{'now':>10}{'change':>10}  result")

    for check in checks:
        change = check.value - check.baseline
        verdict = "ok" if check.passed else "REGRESSION"

        if check.passed and change > tolerance:
            verdict = "ok (better: consider --update)"

        print(f"{check.name:<52}{check.baseline:>10.3f}{check.value:>10.3f}{change:>+10.3f}  {verdict}")

    failed = [c for c in checks if not c.passed]

    for name, shift in shifts.items():
        within = shift <= MAX_SHIFT
        print(f"{name:<52}{'<= ' + str(MAX_SHIFT):>10}{shift:>10.3f}{'':>10}  {'ok' if within else 'REGRESSION'}")

        if not within:
            failed.append(Check(name, shift, MAX_SHIFT, 0.0))

    if missing:
        print(f"Baseline entries that were not measured: {', '.join(missing)}")
        failed.extend(Check(name, float("nan"), stored["metrics"][name], tolerance) for name in missing)

    if failed:
        print(f"\n{len(failed)} check(s) failed.", file=sys.stderr)
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
