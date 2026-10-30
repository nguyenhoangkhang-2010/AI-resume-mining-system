"""
Measures section detection on synthetic multi-format CV corpora.

    python -m scripts.evaluate_sections --out docs/evaluation/section_detection.md

Two corpora are generated into a temporary directory:

- "base": software-engineer content in single, two-column and multi-page
  layouts with six heading styles (app/evaluation/cv_corpus.py);
- "industries": six industries, six page layouts, sections in varying order
  and extra sections that are not extracted (app/evaluation/cv_industries.py).

Both are scored with three configurations, adding one stage at a time:
the heading lexicon alone, plus headings found by their look, plus the
heading classifier.

By default the LLM is replaced by a stub that labels everything "other", so
the numbers show what the deterministic stages and the embedding models
achieve on their own; the number of calls the LLM would have received is
reported next to them. With --heading-llm the real model is asked about
unfamiliar headings only (the cheap, cached call); everything else still
uses the stub.
"""

import argparse
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from loguru import logger

from app.evaluation.cv_corpus import CorpusDocument, CVCorpusBuilder
from app.evaluation.cv_industries import IndustryCorpusBuilder
from app.evaluation.section_eval import (
    DocumentResult,
    SectionScores,
    aggregate,
    group_accuracy,
    score_document,
)
from app.extraction.section.heading_cache import HeadingCache
from app.extraction.section.heading_classifier import HeadingClassifier
from app.extraction.section.section_detector import SectionDetector
from app.extraction.section.section_semantic_classifier import (
    SectionSemanticClassifier,
)
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline

# (name, headings found by look, heading classifier)
CONFIGS = (
    ("words only (lexicon)", False, False),
    ("+ heading style", True, False),
    ("+ heading classifier (+ LLM with --heading-llm)", True, True),
)


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


class HeadingOnlyLLM(CountingNoLLM):
    """Asks the real model about unfamiliar headings; stubs the rest."""

    def __init__(self, classifier) -> None:
        super().__init__()
        self.classifier = classifier
        self.heading_calls = 0
        self.heading_seconds = 0.0
        # Only the last configuration asks the model.
        self.enabled = False

    def classify_heading(self, heading: str) -> Optional[str]:
        if not self.enabled:
            return None

        started = time.perf_counter()
        answer = self.classifier.classify_heading(heading)
        self.heading_seconds += time.perf_counter() - started
        self.heading_calls += 1
        return answer


def table(rows: Dict[str, float], header: str) -> List[str]:
    lines = [f"| {header} | Line accuracy |", "|---|---|"]
    lines += [f"| {name} | {value:.3f} |" for name, value in rows.items()]

    return lines


def evaluate(
    documents: Sequence[CorpusDocument],
    detector: SectionDetector,
) -> List[DocumentResult]:
    pipeline = ResumePipeline(detector, extraction_engine=None)  # type: ignore[arg-type]

    return [
        score_document(document, pipeline.detect_sections(document.path))
        for document in documents
    ]


def section_rows(scores: Dict[str, SectionScores]) -> List[str]:
    lines = [
        "| Section | Precision | Recall | F1 | Lines |",
        "|---|---|---|---|---|",
    ]

    for section, score in scores.items():
        if section != "all":
            lines.append(
                f"| {section} | {score.precision:.3f} | {score.recall:.3f} | "
                f"{score.f1:.3f} | {score.support} |"
            )

    return lines


def report_corpus(
    title: str,
    documents: Sequence[CorpusDocument],
    results: Sequence[DocumentResult],
    keys: Sequence[Tuple[str, str]],
) -> List[str]:
    scores = aggregate(results)

    lines = [
        f"## {title}",
        "",
        f"- Documents: {len(documents)} PDFs, {scores['all'].support} body "
        f"lines scored",
        f"- **Overall line accuracy: {scores['all'].f1:.3f}**",
        "",
        "### Per section",
        "",
        *section_rows(scores),
    ]

    for key, header in keys:
        lines += ["", f"### By {header.lower()}", ""]
        lines += table(group_accuracy(documents, results, key), header)

    return lines + [""]


def ablation_table(
    rows: List[Tuple[str, Dict[str, float], Dict[str, float]]]
) -> List[str]:
    lines = [
        "## Effect of each stage",
        "",
        "Line accuracy by heading wording, adding one stage at a time. "
        "\"alternate\" (base corpus) and \"industry\" (industries corpus) are "
        "headings the lexicon was not built around.",
        "",
        "| Configuration | Base standard | Base alternate | "
        "Industries standard | Industries industry |",
        "|---|---|---|---|---|",
    ]

    for name, base, industries in rows:
        lines.append(
            f"| {name} | {base.get('standard', 0):.3f} | "
            f"{base.get('alternate', 0):.3f} | "
            f"{industries.get('standard', 0):.3f} | "
            f"{industries.get('industry', 0):.3f} |"
        )

    return lines + [""]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/evaluation/section_detection.md")
    parser.add_argument("--per-variant", type=int, default=2)
    parser.add_argument("--industry-per-variant", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--industry-seed", type=int, default=42)
    parser.add_argument(
        "--heading-llm",
        action="store_true",
        help="ask the real LLM about unfamiliar headings (slow the first time)",
    )
    args = parser.parse_args()

    logger.remove()

    semantic = SectionSemanticClassifier()
    heading_classifier = HeadingClassifier()

    fallback: CountingNoLLM

    if args.heading_llm:
        from app.extraction.llm.llm_extractor import LLMExtractor
        from app.extraction.section.section_classifier import SectionClassifier

        fallback = HeadingOnlyLLM(SectionClassifier(LLMExtractor()))
    else:
        fallback = CountingNoLLM()

    heading_cache = HeadingCache() if args.heading_llm else None

    def detector(style: bool, classifier: bool) -> SectionDetector:
        return SectionDetector(
            semantic,
            fallback,  # type: ignore[arg-type]
            heading_classifier=heading_classifier if classifier else None,
            heading_cache=heading_cache if classifier else None,
            use_heading_style=style,
        )

    ablation = []
    calls = {"base": 0, "industries": 0}
    base_results: List[DocumentResult] = []
    industry_results: List[DocumentResult] = []

    with tempfile.TemporaryDirectory() as directory:
        base_documents = CVCorpusBuilder(
            seed=args.seed, per_variant=args.per_variant
        ).build(Path(directory) / "base")

        industry_documents = IndustryCorpusBuilder(
            seed=args.industry_seed, per_variant=args.industry_per_variant
        ).build(Path(directory) / "industries")

        for name, style, classifier in CONFIGS:
            if isinstance(fallback, HeadingOnlyLLM):
                fallback.enabled = classifier

            before = fallback.calls
            base_results = evaluate(base_documents, detector(style, classifier))
            middle = fallback.calls
            industry_results = evaluate(
                industry_documents, detector(style, classifier)
            )

            calls = {
                "base": middle - before,
                "industries": fallback.calls - middle,
            }

            ablation.append(
                (
                    name,
                    group_accuracy(base_documents, base_results, "wording"),
                    group_accuracy(industry_documents, industry_results, "wording"),
                )
            )

    llm_note = (
        "The LLM is asked only about unfamiliar headings (answers are cached); "
        "every other LLM fallback is stubbed. "
        if args.heading_llm
        else "The LLM fallback is stubbed (always \"other\"), so this measures "
        "the deterministic stages and the embedding models only. "
    )

    lines = [
        "# Section detection on synthetic multi-format CV corpora",
        "",
        f"Generated {date.today().isoformat()} by `scripts/evaluate_sections.py` "
        f"(seeds {args.seed}/{args.industry_seed}).",
        "",
        "Each body line has a known true section; a line is correct when the "
        "detector placed it in that section (lines of sections that are not "
        "extracted, such as references or interests, are correct when "
        "dropped). "
        + llm_note
        + "The content is synthetic: results show sensitivity to layout and "
        "headings, not accuracy on real resumes. The heading lexicon and the "
        "example headings of the heading classifier were written by the same "
        "author as the corpora; \"standard\" wording is what the lexicon was "
        "built around, \"alternate\" and \"industry\" wording were chosen to be "
        "different from it.",
        "",
    ]

    if isinstance(fallback, HeadingOnlyLLM):
        lines += [
            f"LLM heading calls: {fallback.heading_calls} "
            f"({fallback.heading_seconds:.0f} s in total)",
            "",
        ]

    lines += ablation_table(ablation)

    lines += report_corpus(
        f"Base corpus, final configuration "
        f"({len({d.style for d in base_documents})} heading styles, "
        f"{len({d.layout for d in base_documents})} layouts, "
        f"{len({d.language for d in base_documents})} languages; "
        f"LLM fallback regions: {calls['base']})",
        base_documents,
        base_results,
        (
            ("wording", "Heading wording"),
            ("style", "Heading style"),
            ("layout", "Layout"),
            ("language", "Language"),
        ),
    )

    lines += report_corpus(
        f"Industries corpus, final configuration "
        f"({len({d.industry for d in industry_documents})} "
        f"industries, {len({d.layout for d in industry_documents})} layouts, "
        f"{len({d.language for d in industry_documents})} languages; "
        f"LLM fallback regions: {calls['industries']})",
        industry_documents,
        industry_results,
        (
            ("wording", "Heading wording"),
            ("layout", "Layout"),
            ("industry", "Industry"),
            ("language", "Language"),
        ),
    )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Report written to {output}")
    print(f"Base line accuracy: {aggregate(base_results)['all'].f1:.3f}")
    print(f"Industries line accuracy: {aggregate(industry_results)['all'].f1:.3f}")


if __name__ == "__main__":
    main()
