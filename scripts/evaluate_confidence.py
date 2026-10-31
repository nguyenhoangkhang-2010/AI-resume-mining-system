"""
Checks whether the confidence score follows the real accuracy of the extraction.

    python -m scripts.evaluate_confidence --out docs/evaluation/confidence_results.md

For every CV the pipeline result is scored twice: the confidence the system
gives itself (app/services/confidence.py) and the accuracy against the known
entities (companies, roles, schools, name). A useful score ranks CVs the way
the accuracy does. The report gives the rank correlation, the chance that a
bad extraction scores lower than a good one, and the accuracy per level.

Two populations are used: synthetic CVs (many, clean, truth known by
construction) and the reviewed real CVs (few; skipped when none exist). The
language model is replaced by one that never answers (`--mode rules`) or the
local model is used (`--mode full`, slow).

The report holds aggregate numbers only and can be published.
"""

import argparse
import atexit
import json
import math
import random
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from loguru import logger

from app.evaluation.cv_industries import IndustryCorpusBuilder
from app.evaluation.field_eval import entities_from_extraction, score_fields
from app.evaluation.pipeline_factory import NoModel, build_pipeline
from app.evaluation.real_cvs import INDEX_NAME, REVIEWED, load_labels
from app.services.confidence import HIGH, LOW, MEDIUM, assess_confidence

# The fields the accuracy is made of. Degrees are left out on purpose: the
# metric for them compares a short level with a full line (see the
# extraction-quality notes), which says little about the extraction.
ACCURACY_FIELDS = ("name", "companies", "roles", "schools")

BAD_BELOW = 0.5


@dataclass
class Point:
    population: str
    score: float
    level: str
    accuracy: float
    components: Dict[str, float]


def accuracy_of(expected: Dict[str, List[str]], extracted: Dict[str, object]) -> float:
    """Mean F1 over the accuracy fields that the CV actually has."""

    scores = score_fields(expected, entities_from_extraction(extracted))  # type: ignore[arg-type]
    values = [scores[name].f1 for name in ACCURACY_FIELDS if scores[name].expected]

    return sum(values) / len(values) if values else math.nan


def ranks(values: Sequence[float]) -> List[float]:
    """Ranks starting at 1; ties share the mean of their positions."""

    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    position = 0

    while position < len(order):
        end = position

        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1

        for index in order[position : end + 1]:
            result[index] = (position + end) / 2 + 1

        position = end + 1

    return result


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) < 3:
        return math.nan

    rx, ry = ranks(x), ranks(y)
    mean_x, mean_y = sum(rx) / len(rx), sum(ry) / len(ry)
    covariance = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry))
    spread_x = math.sqrt(sum((a - mean_x) ** 2 for a in rx))
    spread_y = math.sqrt(sum((b - mean_y) ** 2 for b in ry))

    if spread_x == 0 or spread_y == 0:
        return math.nan

    return covariance / (spread_x * spread_y)


def separation(points: Sequence[Point]) -> float:
    """
    Chance that a CV with a bad extraction gets a lower score than one with a
    good extraction (ties count half); 0.5 is chance, 1.0 is perfect.
    """

    bad = [p.score for p in points if p.accuracy < BAD_BELOW]
    good = [p.score for p in points if p.accuracy >= BAD_BELOW]

    if not bad or not good:
        return math.nan

    wins = sum((g > b) + 0.5 * (g == b) for g in good for b in bad)

    return wins / (len(good) * len(bad))


def synthetic_points(pipeline, args: argparse.Namespace) -> List[Point]:
    directory = Path(tempfile.mkdtemp(prefix="conf_cv_"))
    atexit.register(shutil.rmtree, directory, ignore_errors=True)

    documents = IndustryCorpusBuilder(seed=args.seed).build(directory)
    random.Random(args.seed).shuffle(documents)
    documents = documents[: args.synthetic]

    points: List[Point] = []

    for document in documents:
        extracted = pipeline.process_pdf(document.path)
        confidence = assess_confidence(extracted)
        points.append(
            Point(
                "synthetic",
                confidence.score,
                confidence.level,
                accuracy_of(document.entities, extracted),
                confidence.components,
            )
        )

    return [p for p in points if not math.isnan(p.accuracy)]


def real_points(pipeline, args: argparse.Namespace) -> List[Point]:
    labels_dir = Path(args.labels)

    if not (labels_dir / INDEX_NAME).exists():
        return []

    import json

    labels = [label for label in load_labels(labels_dir) if label.status == REVIEWED]
    folder = Path(
        json.loads((labels_dir / INDEX_NAME).read_text(encoding="utf-8"))["cv_folder"]
    )

    points: List[Point] = []

    for label in labels:
        try:
            extracted = pipeline.process_pdf(folder / label.file)
        except Exception:
            continue

        confidence = assess_confidence(extracted)
        accuracy = accuracy_of(label.entities, extracted)

        if not math.isnan(accuracy):
            points.append(
                Point("real", confidence.score, confidence.level, accuracy, confidence.components)
            )

    return points


def population_lines(name: str, points: Sequence[Point]) -> List[str]:
    if not points:
        return [f"### {name}", "", "No CVs.", ""]

    scores = [p.score for p in points]
    accuracies = [p.accuracy for p in points]
    rho = spearman(scores, accuracies)
    auc = separation(points)
    bad = sum(p.accuracy < BAD_BELOW for p in points)

    lines = [
        f"### {name}",
        "",
        f"- CVs: {len(points)} ({bad} with accuracy below {BAD_BELOW})",
        f"- Mean accuracy: {sum(accuracies) / len(accuracies):.3f}",
        "- Rank correlation between score and accuracy (Spearman): "
        + ("n/a" if math.isnan(rho) else f"{rho:.2f}"),
        "- Chance a bad extraction scores below a good one: "
        + ("n/a" if math.isnan(auc) else f"{auc:.2f}"),
        "",
        "| Level | CVs | Mean accuracy | Share with accuracy below "
        f"{BAD_BELOW} |",
        "|---|---|---|---|",
    ]

    for level in (HIGH, MEDIUM, LOW):
        members = [p for p in points if p.level == level]

        if not members:
            lines.append(f"| {level} | 0 | - | - |")
            continue

        lines.append(
            f"| {level} | {len(members)} | "
            f"{sum(p.accuracy for p in members) / len(members):.3f} | "
            f"{sum(p.accuracy < BAD_BELOW for p in members) / len(members):.2f} |"
        )

    lines.append("")
    lines += band_lines(points)

    return lines


BANDS = ((0.9, 1.01), (0.8, 0.9), (0.7, 0.8), (0.5, 0.7), (0.0, 0.5))


def band_lines(points: Sequence[Point]) -> List[str]:
    """Accuracy per band of score, which shows where the thresholds belong."""

    lines = [
        f"| Score | CVs | Mean accuracy | Share with accuracy below {BAD_BELOW} |",
        "|---|---|---|---|",
    ]

    for low, high in BANDS:
        members = [p for p in points if low <= p.score < high]
        label = f"{low:.1f} to {min(high, 1.0):.1f}"

        if not members:
            lines.append(f"| {label} | 0 | - | - |")
            continue

        lines.append(
            f"| {label} | {len(members)} | "
            f"{sum(p.accuracy for p in members) / len(members):.3f} | "
            f"{sum(p.accuracy < BAD_BELOW for p in members) / len(members):.2f} |"
        )

    lines.append("")

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default="data/real_cv_eval")
    parser.add_argument("--mode", choices=("rules", "full"), default="rules")
    parser.add_argument("--synthetic", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="docs/evaluation/confidence_results.md")
    parser.add_argument("--dump", help="write the measured points here (JSON) for later analysis")
    parser.add_argument("--load", help="report from points written by --dump instead of measuring")
    args = parser.parse_args()

    logger.remove()

    if args.load:
        stored = json.loads(Path(args.load).read_text(encoding="utf-8"))
        populations = [(name, [Point(**p) for p in points]) for name, points in stored]
    else:
        if args.mode == "full":
            from app.extraction.llm.llm_extractor import LLMExtractor

            model = LLMExtractor()
        else:
            model = NoModel()

        pipeline = build_pipeline(model)

        populations = [
            ("Synthetic CVs", synthetic_points(pipeline, args)),
            ("Real CVs (reviewed)", real_points(pipeline, args)),
        ]

    if args.dump:
        Path(args.dump).write_text(
            json.dumps([(name, [asdict(p) for p in points]) for name, points in populations]),
            encoding="utf-8",
        )

    lines = [
        "# Does the confidence score follow the accuracy?",
        "",
        f"Mode: `{args.mode}` ("
        + (
            "no language model; rules, NER and embeddings only"
            if args.mode == "rules"
            else "the local language model answers where the rules do not"
        )
        + f"). Accuracy is the mean F1 over {', '.join(ACCURACY_FIELDS)}.",
        "",
    ]

    for name, points in populations:
        lines += population_lines(name, points)
        print(name, len(points), flush=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
