"""
Times the real resume pipeline (local LLM included) on synthetic CVs and
scores the extracted fields.

    python -m scripts.benchmark_extraction --documents 4 --out docs/evaluation/extraction_speed.md

For every CV it reports where the time goes (each extractor, and the LLM
calls inside them) and how many of the entities the CV was generated from
(companies, roles, schools, skills ...) were found. Run it before and after a
change to see the effect on both speed and quality. It needs the GGUF model,
so it is a script and not a test.
"""

import argparse
import atexit
import shutil
import statistics
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from loguru import logger

from app.evaluation.cv_industries import IndustryCorpusBuilder, IndustryDocument
from app.extraction.rules import stats
from app.evaluation.field_eval import (
    FIELDS,
    FieldScore,
    aggregate_fields,
    entities_from_extraction,
    field_table,
    score_fields,
)

# (industry, layout) of the benchmark documents, English only; chosen to
# cover different content and page structures.
SAMPLE = (
    ("healthcare", "single"),
    ("finance", "two_column"),
    ("software", "timeline"),
    ("education", "sidebar_right"),
    ("mechanical", "banner_two_column"),
    ("marketing", "long"),
)


@dataclass
class PlainDocument:
    """A CV from a folder: there is no truth to score against."""

    id: str
    path: Path
    entities: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class CallRecord:
    label: str
    input_chars: int
    output_chars: int
    seconds: float


@dataclass
class DocumentTiming:
    document: str
    total: float = 0.0
    sections: float = 0.0
    extractors: Dict[str, float] = field(default_factory=dict)
    calls: List[CallRecord] = field(default_factory=list)
    scores: Dict[str, FieldScore] = field(default_factory=dict)
    answered_by: Dict[str, int] = field(default_factory=dict)


class RecordingLLM:
    """Wraps an LLM extractor and records every call."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.calls: List[CallRecord] = []

    def extract_info(
        self,
        text: str,
        prompt_template: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
    ) -> str:
        label = _label(prompt_template)
        started = time.perf_counter()
        output = self.inner.extract_info(text, prompt_template, max_new_tokens)

        self.calls.append(
            CallRecord(
                label, len(text), len(output or ""), time.perf_counter() - started
            )
        )

        return output

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)


def _label(template: Optional[str]) -> str:
    """The extractor (or section step) a prompt belongs to, by identity."""

    if not template:
        return "raw"

    for name, prompt in _prompts().items():
        if template is prompt or template == prompt:
            return name

    text = " ".join(template.split()).lower()

    if "single fragment" in text:
        return "section (region)"

    if "heading of a section" in text:
        return "section (heading)"

    return "other"


def _prompts() -> Dict[str, str]:
    from app.extraction.certifications.certification_extractor import (
        CertificationExtractor,
    )
    from app.extraction.education.education_extractor import EducationExtractor
    from app.extraction.experience.experience_extractor import ExperienceExtractor
    from app.extraction.projects.project_extractor import ProjectExtractor
    from app.extraction.summary.summary_extractor import SummaryExtractor

    return {
        "summary": SummaryExtractor.EXTRACTION_PROMPT,
        "education": EducationExtractor.EXTRACTION_PROMPT,
        "experience": ExperienceExtractor.EXTRACTION_PROMPT,
        "projects": ProjectExtractor.EXTRACTION_PROMPT,
        "certifications": CertificationExtractor.EXTRACTION_PROMPT,
    }


class TimedExtractor:
    def __init__(self, name: str, inner: Any, sink: Dict[str, float]) -> None:
        self.name, self.inner, self.sink = name, inner, sink

    def extract(self, *args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()

        try:
            return self.inner.extract(*args, **kwargs)
        finally:
            self.sink[self.name] = (
                self.sink.get(self.name, 0.0) + time.perf_counter() - started
            )


def build_pipeline(recorder: RecordingLLM, timings: Dict[str, float]):
    from app.extraction.extraction_engine import ExtractionEngine
    from app.extraction.section.heading_cache import HeadingCache
    from app.extraction.section.heading_classifier import HeadingClassifier
    from app.extraction.section.section_classifier import SectionClassifier
    from app.extraction.section.section_detector import SectionDetector
    from app.extraction.section.section_semantic_classifier import (
        SectionSemanticClassifier,
    )
    from app.resume_processing.pipelines.resume_pipeline import ResumePipeline

    detector = SectionDetector(
        semantic_classifier=SectionSemanticClassifier(),
        llm_classifier=SectionClassifier(llm_extractor=recorder),  # type: ignore[arg-type]
        heading_classifier=HeadingClassifier(),
        heading_cache=HeadingCache(),
    )
    engine = ExtractionEngine(llm_extractor=recorder)  # type: ignore[arg-type]

    engine.extractors = {
        name: TimedExtractor(name, extractor, timings)
        for name, extractor in engine.extractors.items()
    }

    return ResumePipeline(detector, engine)


def benchmark(
    documents: Sequence[Any],
    pipeline: Any,
    recorder: RecordingLLM,
    timings: Dict[str, float],
) -> List[DocumentTiming]:
    results: List[DocumentTiming] = []

    for document in documents:
        recorder.calls.clear()
        timings.clear()
        stats.reset()

        started = time.perf_counter()
        extracted = pipeline.process_pdf(document.path)
        total = time.perf_counter() - started

        entry = DocumentTiming(document.id, total=total)
        entry.extractors = dict(timings)
        entry.calls = list(recorder.calls)
        entry.sections = total - sum(entry.extractors.values())
        entry.answered_by = stats.snapshot()
        entry.scores = score_fields(
            document.entities, entities_from_extraction(extracted)
        )

        results.append(entry)
        print(
            f"{document.id}: {total:.0f}s, {len(entry.calls)} LLM calls",
            flush=True,
        )

    return results


def report(results: Sequence[DocumentTiming], title: str) -> List[str]:
    totals = [r.total for r in results]

    lines = [
        f"## {title}",
        "",
        f"- Documents: {len(results)}",
        f"- Seconds per CV: mean {statistics.mean(totals):.0f}, "
        f"min {min(totals):.0f}, max {max(totals):.0f}",
        f"- LLM calls per CV: {statistics.mean(len(r.calls) for r in results):.1f}",
        "",
        "### Where the time goes (mean seconds per CV)",
        "",
        "| Stage | Seconds | LLM calls | LLM seconds |",
        "|---|---|---|---|",
    ]

    by_extractor: Dict[str, List[float]] = defaultdict(list)

    for r in results:
        for name, seconds in r.extractors.items():
            by_extractor[name].append(seconds)

    by_label: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    for r in results:
        for call in r.calls:
            count, seconds = by_label[call.label]
            by_label[call.label] = (count + 1, seconds + call.seconds)

    n = len(results)
    lines.append(
        f"| sections (parse, layout, headings) | "
        f"{statistics.mean(r.sections for r in results):.1f} | "
        f"{by_label['section (region)'][0] / n + by_label['section (heading)'][0] / n:.1f} | "
        f"{(by_label['section (region)'][1] + by_label['section (heading)'][1]) / n:.1f} |"
    )

    for name, values in by_extractor.items():
        count, seconds = by_label.get(name, (0, 0.0))
        lines.append(
            f"| {name} | {sum(values) / n:.1f} | {count / n:.1f} | {seconds / n:.1f} |"
        )

    answered: Dict[str, int] = defaultdict(int)

    for r in results:
        for key, count in r.answered_by.items():
            answered[key] += count

    if answered:
        lines += ["", "### Sections read by rules or by the model", ""]
        lines += ["| Section | Rules | Model |", "|---|---|---|"]

        for name in sorted({key.split(".")[0] for key in answered}):
            lines.append(
                f"| {name} | {answered.get(name + '.rules', 0)} | "
                f"{answered.get(name + '.model', 0)} |"
            )

    fields = aggregate_fields(r.scores for r in results)

    if any(score.expected for score in fields.values()):
        lines += [
            "",
            "### Fields found (micro-averaged over the documents)",
            "",
            field_table(fields),
        ]

    lines.append("")

    return lines


def synthetic_documents(args: argparse.Namespace) -> List[IndustryDocument]:
    documents: List[IndustryDocument] = []
    directory = Path(tempfile.mkdtemp(prefix="bench_cv_"))
    atexit.register(shutil.rmtree, directory, ignore_errors=True)

    for industry, layout in SAMPLE[: args.documents]:
        documents += IndustryCorpusBuilder(
            seed=args.seed,
            industries=[industry],
            layouts=[layout],
            wordings=("industry",),
        ).build(directory / f"{industry}_{layout}")

    return [d for d in documents if d.language == "en"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=int, default=len(SAMPLE))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="docs/evaluation/extraction_speed.md")
    parser.add_argument("--title", default="Extraction speed and quality")
    parser.add_argument(
        "--folder",
        help="time your own PDFs instead of the synthetic CVs (no scores; "
        "file names are not printed or written)",
    )
    args = parser.parse_args()

    logger.remove()

    from app.extraction.llm.llm_extractor import LLMExtractor

    recorder = RecordingLLM(LLMExtractor())
    timings: Dict[str, float] = {}
    pipeline = build_pipeline(recorder, timings)

    if args.folder:
        pdfs = sorted(Path(args.folder).glob("*.pdf"))[: args.documents]
        results = benchmark(
            [PlainDocument(f"cv-{n}", path) for n, path in enumerate(pdfs, 1)],
            pipeline,
            recorder,
            timings,
        )
        source = "CVs from a folder (no scores)"
    else:
        results = benchmark(
            synthetic_documents(args), pipeline, recorder, timings
        )
        source = f"English synthetic CVs (seed {args.seed})"

    lines = [
        "# Extraction speed",
        "",
        f"Generated {date.today().isoformat()} by `scripts/benchmark_extraction.py` "
        f"({source}, local GGUF model on CPU).",
        "",
        *report(results, args.title),
    ]

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Report written to {output}")
    print("Fields:", ", ".join(FIELDS))


if __name__ == "__main__":
    main()
