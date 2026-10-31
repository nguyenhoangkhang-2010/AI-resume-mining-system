"""
Prepares a private, labelled set of real CVs.

    python -m scripts.real_cv_prepare pick  --folder data/uploads --count 40
    python -m scripts.real_cv_prepare draft --folder data/uploads
    python -m scripts.real_cv_prepare open  cv-001      # PDF and label side by side
    python -m scripts.real_cv_prepare mark  cv-001      # after correcting it
    python -m scripts.real_cv_prepare check

Everything is written under data/real_cv_eval (git-ignored). The output of
this script names no file and prints no CV text: the CVs are personal data.
After `draft`, open each PDF, correct its label file (entities, sections,
tags) and set "status" to "reviewed"; `check` lists what is left to do.
"""

import argparse
import json
import webbrowser
from collections import Counter
from pathlib import Path
from typing import List, Optional

from loguru import logger

from app.evaluation.real_cvs import (
    DRAFT,
    INDEX_NAME,
    REVIEWED,
    Candidate,
    draft_label,
    guess_language,
    load_labels,
    near_duplicate_groups,
    pick_diverse,
    save_label,
    summarize_candidates,
    validate,
)

DEFAULT_LABELS = "data/real_cv_eval"
PICKED = "picked.json"


def candidate_from_pdf(path: Path) -> Candidate:
    from app.resume_processing.layout.layout_analyzer import LayoutAnalyzer
    from app.resume_processing.layout.layout_representation import LayoutDocument
    from app.resume_processing.layout.semantic_region_analyzer import (
        SemanticRegionAnalyzer,
    )
    from app.resume_processing.parsers.pdf_parser import PDFParser

    parsed = PDFParser.parse(path)
    layout = LayoutAnalyzer().analyze(LayoutDocument.from_parser_result(parsed))
    analyzer = SemanticRegionAnalyzer()
    columns = max(
        (len(analyzer._detect_columns(page.blocks, page.width)) for page in layout.pages),
        default=1,
    )
    text = parsed.get("text", "")

    return Candidate(
        name=path.name,
        pages=len(parsed.get("pages", [])) or 1,
        columns=columns,
        language=guess_language(text),
        chars=len(text),
        text=text,
    )


def print_summary(label: str, candidates: List[Candidate]) -> None:
    counts = summarize_candidates(candidates)

    print(f"{label}: {len(candidates)} CVs")

    for key, values in counts.items():
        print(f"  {key}: " + ", ".join(f"{v}: {n}" for v, n in sorted(values.items())))


def command_pick(args: argparse.Namespace) -> None:
    folder = Path(args.folder)
    pdfs = sorted(folder.glob("*.pdf"))
    candidates = []

    for path in pdfs:
        try:
            candidates.append(candidate_from_pdf(path))
        except Exception:
            logger.warning("A PDF could not be read and is skipped.")

    groups = near_duplicate_groups(candidates)
    sizes = sorted((len(g) for g in groups), reverse=True)
    chosen = pick_diverse(candidates, args.count, args.per_template)

    print_summary("Found", candidates)
    print(f"Near-identical text groups (sizes): {sizes[:10]}")
    print_summary("Picked", chosen)

    target = Path(args.labels)
    target.mkdir(parents=True, exist_ok=True)
    (target / PICKED).write_text(
        json.dumps(
            {"cv_folder": str(folder), "files": [c.name for c in chosen]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Choice saved in {target / PICKED}")


def command_draft(args: argparse.Namespace) -> None:
    from app.evaluation.pipeline_factory import NoModel, build_pipeline

    target = Path(args.labels)
    picked_path = target / PICKED
    folder = Path(args.folder)

    if picked_path.is_file():
        files = json.loads(picked_path.read_text(encoding="utf-8"))["files"]
    else:
        files = [p.name for p in sorted(folder.glob("*.pdf"))]

    if args.llm:
        from app.extraction.llm.llm_extractor import LLMExtractor

        model = LLMExtractor()
    else:
        model = NoModel()

    pipeline = build_pipeline(model)

    existing = {label.file: label.id for label in load_labels(target)}
    number = len(existing)
    written = skipped = 0

    for name in files:
        if name in existing and not args.force:
            skipped += 1
            continue

        number += 1
        cv_id = existing.get(name) or f"cv-{number:03d}"
        path = folder / name

        try:
            extracted = pipeline.process_pdf(path)
            sections = pipeline.detect_sections(path)
            candidate = candidate_from_pdf(path)
        except Exception:
            logger.warning("{} could not be processed and is skipped.", cv_id)
            continue

        tags = {
            "language": candidate.language,
            "layout": "single" if candidate.columns == 1 else "multi_column",
            "pages": str(min(candidate.pages, 4)),
            "industry": "",
        }
        save_label(target, draft_label(cv_id, name, extracted, sections, tags))
        written += 1

    (target / INDEX_NAME).write_text(
        json.dumps({"cv_folder": str(folder)}, indent=2), encoding="utf-8"
    )
    print(f"Drafts written: {written}, already present and left alone: {skipped}")
    print("Next: open each PDF, correct its label file, set status to 'reviewed'.")


def command_check(args: argparse.Namespace) -> None:
    labels = load_labels(Path(args.labels))
    status = Counter(label.status for label in labels)
    problems = validate(labels)

    print(f"{len(labels)} label files: " + ", ".join(f"{k}: {v}" for k, v in sorted(status.items())))

    for key in ("language", "layout", "industry"):
        values = Counter(
            label.tags.get(key) or "(empty)"
            for label in labels
            if label.status == REVIEWED
        )
        print(f"  reviewed by {key}: " + ", ".join(f"{k}: {v}" for k, v in sorted(values.items())))

    todo = [label.id for label in labels if label.status == DRAFT]
    print(f"Still drafts: {len(todo)}" + (f" ({', '.join(todo[:10])}{' ...' if len(todo) > 10 else ''})" if todo else ""))

    if problems:
        print("Problems:")

        for problem in problems:
            print("  " + problem)

        raise SystemExit(1)

    print("No problems found.")


def command_open(args: argparse.Namespace) -> None:
    target = Path(args.labels)
    folder = _cv_folder(target, args.folder)
    labels = {label.id: label for label in load_labels(target)}

    for cv_id in args.ids:
        label = labels.get(cv_id)

        if label is None:
            print(f"{cv_id}: no such label")
            continue

        webbrowser.open((folder / label.file).resolve().as_uri())
        webbrowser.open((target / f"{cv_id}.json").resolve().as_uri())
        print(f"{cv_id}: opened")


def command_mark(args: argparse.Namespace) -> None:
    """Marks labels as reviewed, if they pass validation."""

    target = Path(args.labels)
    labels = {label.id: label for label in load_labels(target)}
    ids = list(labels) if args.all else args.ids

    for cv_id in ids:
        label = labels.get(cv_id)

        if label is None:
            print(f"{cv_id}: no such label")
            continue

        label.status = REVIEWED
        problems = validate([label])

        if problems:
            print(chr(10).join(problems))
            continue

        save_label(target, label)
        print(f"{cv_id}: marked as reviewed")


def _cv_folder(labels: Path, given: Optional[str]) -> Path:
    if given:
        return Path(given)

    index = json.loads((labels / INDEX_NAME).read_text(encoding="utf-8"))

    return Path(index["cv_folder"])


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default=DEFAULT_LABELS)
    commands = parser.add_subparsers(dest="command", required=True)

    pick = commands.add_parser("pick", help="choose a varied subset of the CVs")
    pick.add_argument("--folder", default="data/uploads")
    pick.add_argument("--count", type=int, default=40)
    pick.add_argument("--per-template", type=int, default=2)
    pick.set_defaults(run=command_pick)

    draft = commands.add_parser("draft", help="write draft label files to correct")
    draft.add_argument("--folder", default="data/uploads")
    draft.add_argument("--llm", action="store_true", help="draft with the local LLM (slow)")
    draft.add_argument("--force", action="store_true", help="overwrite existing labels")
    draft.set_defaults(run=command_draft)

    opener = commands.add_parser("open", help="open a CV and its label file")
    opener.add_argument("ids", nargs="+")
    opener.add_argument("--folder", help="default: the folder used by `draft`")
    opener.set_defaults(run=command_open)

    mark = commands.add_parser("mark", help="mark corrected labels as reviewed")
    mark.add_argument("ids", nargs="*")
    mark.add_argument("--all", action="store_true")
    mark.set_defaults(run=command_mark)

    check = commands.add_parser("check", help="validate the label files")
    check.set_defaults(run=command_check)

    args = parser.parse_args(argv)
    logger.remove()
    args.run(args)


if __name__ == "__main__":
    main()
