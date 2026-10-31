"""
Measures what the French, Spanish, German, Portuguese and Russian vocabulary
files add, on a small synthetic CV set (app/evaluation/cv_languages.py).

    python -m scripts.evaluate_languages --out docs/evaluation/multilingual_results.md

Every CV is read twice by the same pipeline: with only the English and
Vietnamese vocabulary (the situation before those files existed) and with all
the built-in files. The language model is replaced by one that never answers,
so the numbers show what headings, rules, NER and embeddings do on their own.

The CVs are invented, tiny in number and written by the same hand as the
vocabulary files; the report shows that the support works, not how accurate it
is on real CVs of those languages.
"""

import argparse
import atexit
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence

from loguru import logger

from app.evaluation.cv_languages import LANGUAGES, LanguageDocument, build_language_corpus
from app.evaluation.field_eval import (
    FieldScore,
    aggregate_fields,
    entities_from_extraction,
    score_fields,
)
from app.evaluation.pipeline_factory import NoModel, build_pipeline
from app.evaluation.section_eval import score_document
from app.extraction.rules import vocabulary

REPORTED_FIELDS = ("name", "companies", "roles", "schools", "degrees", "skills", "certifications")


def use_vocabulary(directory: Path) -> None:
    vocabulary.BUILTIN_DIRECTORY = directory
    vocabulary.clear_cache()


def measure(pipeline, documents: Sequence[LanguageDocument]):
    """Per language: (line accuracy, field scores) over its documents."""

    correct: Dict[str, int] = defaultdict(int)
    total: Dict[str, int] = defaultdict(int)
    fields: Dict[str, List[Dict[str, FieldScore]]] = defaultdict(list)

    for document in documents:
        result = score_document(document, pipeline.detect_sections(document.path))
        correct[document.language] += result.correct
        total[document.language] += result.total

        extracted = pipeline.process_pdf(document.path)
        fields[document.language].append(
            score_fields(document.entities, entities_from_extraction(extracted))
        )

    return {
        language: (
            correct[language] / total[language],
            aggregate_fields(fields[language]),
        )
        for language in total
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/evaluation/multilingual_results.md")
    args = parser.parse_args()

    logger.remove()

    work = Path(tempfile.mkdtemp(prefix="lang_cv_"))
    atexit.register(shutil.rmtree, work, ignore_errors=True)

    documents = build_language_corpus(work / "cvs")
    built_in = vocabulary.BUILTIN_DIRECTORY

    baseline_dir = work / "baseline_vocabulary"
    baseline_dir.mkdir()

    for name in ("en.json", "vi.json"):
        shutil.copy(built_in / name, baseline_dir / name)

    pipeline = build_pipeline(NoModel())

    try:
        use_vocabulary(baseline_dir)
        before = measure(pipeline, documents)
        use_vocabulary(built_in)
        after = measure(pipeline, documents)
    finally:
        use_vocabulary(built_in)

    present = [language for language in LANGUAGES if language in after]
    counts = {language: sum(d.language == language for d in documents) for language in present}

    lines = [
        "# Other languages: what the vocabulary files add",
        "",
        "Synthetic CVs (invented people, three per language, one column), read by the "
        "pipeline without a language model. *Before* has only the English and "
        "Vietnamese vocabulary, *after* all built-in files. Line accuracy is the share "
        "of lines placed in the right section; the field columns are F1 over the "
        "entities of the language's CVs.",
        "",
        "| Language | CVs | Lines before | Lines after | "
        + " | ".join(f"{name} before → after" for name in REPORTED_FIELDS)
        + " |",
        "|---|---|---|---|" + "---|" * len(REPORTED_FIELDS),
    ]

    for language in present:
        cells = [
            f"{before[language][1][name].f1:.2f} → {after[language][1][name].f1:.2f}"
            for name in REPORTED_FIELDS
        ]
        lines.append(
            f"| {language} | {counts[language]} | {before[language][0]:.3f} | "
            f"{after[language][0]:.3f} | " + " | ".join(cells) + " |"
        )

    lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
