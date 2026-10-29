"""
Measures section detection on a synthetic multi-format CV corpus.

    python -m scripts.evaluate_sections --out docs/evaluation/section_detection.md

The corpus (PDFs with known sections) is generated into a temporary
directory. The LLM fallback is replaced by a stub that labels everything
"other", so the numbers show what the deterministic stages achieve on their
own; the share of regions that would call the LLM is reported separately.
"""

import argparse
import tempfile
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger

from app.evaluation.cv_corpus import CVCorpusBuilder
from app.evaluation.section_eval import (
    aggregate,
    group_accuracy,
    score_document,
)
from app.extraction.section.section_detector import SectionDetector
from app.extraction.section.section_semantic_classifier import (
    SectionSemanticClassifier,
)
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline


class CountingNoLLM:
    """Stands in for the LLM fallback and counts how often it is needed."""

    def __init__(self) -> None:
        self.calls = 0

    def classify_single(self, text: str) -> Tuple[str, float]:
        self.calls += 1
        return "other", 0.0

    def classify_document(self, lines: List[str]) -> List[dict]:
        self.calls += 1
        return []


def table(rows: Dict[str, float], header: str) -> List[str]:
    lines = [f"| {header} | Line accuracy |", "|---|---|"]
    lines += [f"| {name} | {value:.3f} |" for name, value in rows.items()]

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/evaluation/section_detection.md")
    parser.add_argument("--per-variant", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logger.remove()

    with tempfile.TemporaryDirectory() as directory:
        documents = CVCorpusBuilder(
            seed=args.seed, per_variant=args.per_variant
        ).build(Path(directory))

        fallback = CountingNoLLM()
        detector = SectionDetector(SectionSemanticClassifier(), fallback)
        pipeline = ResumePipeline(detector, extraction_engine=None)  # type: ignore[arg-type]

        results = [
            score_document(document, pipeline.detect_sections(document.path))
            for document in documents
        ]

    scores = aggregate(results)

    lines = [
        "# Section detection on a synthetic multi-format CV corpus",
        "",
        f"Generated {date.today().isoformat()} by `scripts/evaluate_sections.py` "
        f"(seed {args.seed}).",
        "",
        f"- Documents: {len(documents)} PDFs "
        f"({len({d.style for d in documents})} heading styles x "
        f"{len({d.layout for d in documents})} layouts x "
        f"{len({d.language for d in documents})} languages, plus "
        f"{sum(d.wording == 'alternate' for d in documents)} documents with "
        f"alternate heading wording)",
        f"- Body lines scored: {scores['all'].support}",
        f"- Regions that would call the LLM fallback: {fallback.calls}",
        "",
        "Each body line has a known true section; a line is correct when the "
        "detector placed it in that section. The LLM fallback is disabled "
        "(stubbed), so this measures the deterministic stages only. The "
        "content is synthetic: results show sensitivity to layout and "
        "headings, not accuracy on real resumes. The heading lexicon was "
        "written around the \"standard\" wording, so those numbers are "
        "optimistic; \"alternate\" wording uses titles the lexicon was not "
        "designed around.",
        "",
        f"**Overall line accuracy: {scores['all'].f1:.3f}**",
        "",
        "## Per section",
        "",
        "| Section | Precision | Recall | F1 | Lines |",
        "|---|---|---|---|---|",
    ]

    for section, score in scores.items():
        if section != "all":
            lines.append(
                f"| {section} | {score.precision:.3f} | {score.recall:.3f} | "
                f"{score.f1:.3f} | {score.support} |"
            )

    for key, header in (
        ("wording", "Heading wording"),
        ("style", "Heading style"),
        ("layout", "Layout"),
        ("language", "Language"),
    ):
        lines += ["", f"## By {header.lower()}", ""]
        lines += table(group_accuracy(documents, results, key), header)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Report written to {output}")
    print(f"Overall line accuracy: {scores['all'].f1:.3f}")


if __name__ == "__main__":
    main()
