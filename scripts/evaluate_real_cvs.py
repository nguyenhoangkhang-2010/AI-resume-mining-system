"""
Scores the pipeline on the reviewed real CVs.

    python -m scripts.evaluate_real_cvs --mode rules --out docs/evaluation/real_cv_results.md
    python -m scripts.evaluate_real_cvs --mode full  --out docs/evaluation/real_cv_results.md

`rules` replaces the language model by one that never answers, so the report
shows what the rules, NER and embedding models achieve alone (fast, no model
needed). `full` uses the local LLM exactly as the API does (slow).

The report written to --out has aggregate numbers only and can be published.
A second file next to the labels (local_report.md) names the weakest CVs by
their anonymous ids so you can look at them; it stays on your machine.
"""

import argparse
import json
import time
from pathlib import Path
from typing import List

from loguru import logger

from app.evaluation.pipeline_factory import NoModel, build_pipeline
from app.evaluation.real_cv_scoring import CVResult, report, score_cv, weakest
from app.evaluation.real_cvs import INDEX_NAME, REVIEWED, load_labels
from app.extraction.rules import stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default="data/real_cv_eval")
    parser.add_argument("--cv-folder", help="default: the folder recorded in index.json")
    parser.add_argument("--mode", choices=("rules", "full"), default="rules")
    parser.add_argument("--out", default="docs/evaluation/real_cv_results.md")
    parser.add_argument("--title", default="Results on real CVs")
    parser.add_argument("--note", default="", help="a sentence added under the intro of the report")
    args = parser.parse_args()

    logger.remove()

    labels_dir = Path(args.labels)
    labels = [label for label in load_labels(labels_dir) if label.status == REVIEWED]

    if not labels:
        raise SystemExit("No reviewed labels found. See docs/evaluation/real_cv_README.md.")

    folder = args.cv_folder

    if folder is None:
        index = json.loads((labels_dir / INDEX_NAME).read_text(encoding="utf-8"))
        folder = index["cv_folder"]

    if args.mode == "full":
        from app.extraction.llm.llm_extractor import LLMExtractor

        model = LLMExtractor()
    else:
        model = NoModel()

    pipeline = build_pipeline(model)
    results: List[CVResult] = []

    for label in labels:
        path = Path(folder) / label.file
        stats.reset()
        started = time.perf_counter()

        try:
            extracted = pipeline.process_pdf(path)
            sections = pipeline.detect_sections(path)
        except Exception:
            print(f"{label.id}: could not be processed")
            continue

        seconds = time.perf_counter() - started
        results.append(score_cv(label, extracted, sections, seconds, stats.snapshot()))
        print(f"{label.id}: {seconds:.0f}s", flush=True)

    mode_text = (
        "rules, NER and embeddings only (language model off)"
        if args.mode == "rules"
        else "full pipeline with the local language model"
    )
    lines = report(results, args.title, mode_text, note=args.note)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    local = labels_dir / "local_report.md"
    local.write_text(
        "# Weakest CVs (core entity F1), anonymous ids\n\n"
        + "\n".join(f"- {cv_id}: {score:.3f}" for cv_id, score in weakest(results))
        + "\n",
        encoding="utf-8",
    )

    print(f"Report written to {output}; weakest CVs listed in {local}")


if __name__ == "__main__":
    main()
