"""
Scores the pipeline against reviewed labels of real CVs and writes a report
that contains only aggregate numbers (no text, names or file names).

With a few dozen CVs the numbers are noisy, so every headline figure carries
a 95% bootstrap interval over CVs, and groups of fewer than MIN_GROUP CVs are
not reported on their own.
"""

import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from app.evaluation.field_eval import (
    FIELDS,
    FieldScore,
    aggregate_fields,
    entities_from_extraction,
    score_fields,
)
from app.evaluation.real_cvs import (
    MIN_GROUP,
    REVIEWED,
    SECTIONS,
    LabelFile,
    present_sections,
)

# Fields whose values the CV states and nothing else defines; "skills" is
# reported separately because the extractor draws on a large taxonomy and
# returns skills a person would not list.
CORE_FIELDS = ("name", "companies", "roles", "schools", "degrees", "certifications")

BOOTSTRAP_SAMPLES = 500


@dataclass
class CVResult:
    id: str
    tags: Dict[str, str]
    fields: Dict[str, FieldScore]
    predicted_sections: List[str]
    true_sections: List[str]
    seconds: float = 0.0
    answered_by: Dict[str, int] = field(default_factory=dict)


def score_cv(
    label: LabelFile,
    extracted: Mapping[str, object],
    detected_sections: Mapping[str, Sequence[str]],
    seconds: float = 0.0,
    answered_by: Optional[Mapping[str, int]] = None,
) -> CVResult:
    if label.status != REVIEWED:
        raise ValueError(f"{label.id} has not been reviewed")

    return CVResult(
        id=label.id,
        tags=dict(label.tags),
        fields=score_fields(label.entities, entities_from_extraction(extracted)),
        predicted_sections=present_sections(detected_sections),
        true_sections=[s for s in label.sections_present if s in SECTIONS],
        seconds=seconds,
        answered_by=dict(answered_by or {}),
    )


# ---------------------------------------------------------------- metrics


def micro(results: Sequence[CVResult], names: Sequence[str] = FIELDS) -> Dict[str, FieldScore]:
    scores = aggregate_fields(r.fields for r in results)

    return {name: scores[name] for name in names}


def core_f1(results: Sequence[CVResult]) -> float:
    """Micro F1 over the core fields taken together."""

    hits = correct = expected = found = 0.0

    for result in results:
        for name in CORE_FIELDS:
            score = result.fields[name]
            hits += score.recall * score.expected
            correct += score.precision * score.found
            expected += score.expected
            found += score.found

    precision = correct / found if found else 0.0
    recall = hits / expected if expected else 0.0

    return (
        2 * precision * recall / (precision + recall) if precision + recall else 0.0
    )


def _field_f1(name: str) -> Callable[[Sequence[CVResult]], float]:
    def statistic(sample: Sequence[CVResult]) -> float:
        score = micro(sample, (name,))[name]

        # With nothing expected and nothing found F1 is undefined, not 0.
        return score.f1 if score.expected or score.found else math.nan

    return statistic


def bootstrap_interval(
    results: Sequence[CVResult],
    statistic: Callable[[Sequence[CVResult]], float],
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = 0,
) -> Tuple[float, float]:
    """
    95% interval of a statistic, resampling whole CVs. Resamples for which
    the statistic is undefined (NaN) are left out.
    """

    if len(results) < 2:
        value = statistic(results) if results else 0.0

        return (0.0, 0.0) if math.isnan(value) else (value, value)

    rng = random.Random(seed)
    values = sorted(
        value
        for value in (
            statistic([rng.choice(results) for _ in results]) for _ in range(samples)
        )
        if not math.isnan(value)
    )

    if not values:
        return 0.0, 0.0

    return (
        values[int(0.025 * len(values))],
        values[max(0, int(0.975 * len(values)) - 1)],
    )


def section_presence(results: Sequence[CVResult]) -> Dict[str, Tuple[float, float, int]]:
    """Per section: (precision, recall, CVs that really have it)."""

    table: Dict[str, Tuple[float, float, int]] = {}

    for section in SECTIONS:
        true = {r.id for r in results if section in r.true_sections}
        predicted = {r.id for r in results if section in r.predicted_sections}
        both = len(true & predicted)

        table[section] = (
            both / len(predicted) if predicted else 0.0,
            both / len(true) if true else 0.0,
            len(true),
        )

    return table


def groups(results: Sequence[CVResult], key: str) -> Dict[str, List[CVResult]]:
    """CVs by tag value; values with fewer than MIN_GROUP CVs are merged."""

    by_value: Dict[str, List[CVResult]] = defaultdict(list)

    for result in results:
        by_value[result.tags.get(key) or "untagged"].append(result)

    merged: Dict[str, List[CVResult]] = {}
    small: List[CVResult] = []

    for value, members in sorted(by_value.items()):
        if len(members) >= MIN_GROUP:
            merged[value] = members
        else:
            small.extend(members)

    if small:
        merged[f"other (fewer than {MIN_GROUP} each)"] = small

    return merged


# ----------------------------------------------------------------- report


def report(
    results: Sequence[CVResult],
    title: str,
    mode: str,
    group_keys: Sequence[str] = ("language", "layout", "industry"),
    note: str = "",
) -> List[str]:
    if not results:
        return [f"# {title}", "", "No reviewed CVs."]

    lines = [
        f"# {title}",
        "",
        f"Mode: **{mode}**. {len(results)} reviewed real CVs. Only aggregate "
        "numbers are published; the CVs and their labels stay on the "
        "machine of their owner.",
        "",
        "Intervals are 95% bootstrap intervals over CVs; with this few CVs "
        "they are wide, and a difference smaller than the interval is not "
        "evidence of anything.",
        "",
    ]

    if note:
        lines += [note, ""]

    overall = core_f1(results)
    low, high = bootstrap_interval(results, core_f1)

    lines += [
        f"**Core entity F1 (name, companies, roles, schools, degrees, "
        f"certificates): {overall:.3f} [{low:.3f}, {high:.3f}]**",
        "",
        "## Fields",
        "",
        "| Field | Precision | Recall | F1 | F1 interval | Expected | Found |",
        "|---|---|---|---|---|---|---|",
    ]

    scores = micro(results)

    for name in FIELDS:
        score = scores[name]
        f1_low, f1_high = bootstrap_interval(results, _field_f1(name))
        lines.append(
            f"| {name} | {score.precision:.3f} | {score.recall:.3f} | "
            f"{score.f1:.3f} | [{f1_low:.3f}, {f1_high:.3f}] | "
            f"{score.expected} | {score.found} |"
        )

    lines += [
        "",
        "`skills` precision is low by construction: the extractor returns "
        "taxonomy skills that a person would not list; read its recall.",
        "",
        "## Sections found",
        "",
        "| Section | Precision | Recall | CVs that have it |",
        "|---|---|---|---|",
    ]

    for section, (precision, recall, count) in section_presence(results).items():
        lines.append(f"| {section} | {precision:.3f} | {recall:.3f} | {count} |")

    for key in group_keys:
        members = groups(results, key)

        if len(members) < 2 and "untagged" in members:
            continue

        lines += ["", f"## By {key}", "", f"| {key} | CVs | Core entity F1 |", "|---|---|---|"]

        for value, group in members.items():
            lines.append(f"| {value} | {len(group)} | {core_f1(group):.3f} |")

    times = [r.seconds for r in results if r.seconds > 0]

    if times:
        lines += [
            "",
            "## Time",
            "",
            f"Seconds per CV: mean {statistics.mean(times):.1f}, "
            f"median {statistics.median(times):.1f}, max {max(times):.1f}.",
        ]

    answered: Dict[str, int] = defaultdict(int)

    for result in results:
        for key, count in result.answered_by.items():
            answered[key] += count

    if answered:
        lines += ["", "## Sections read by rules or by the model", ""]
        lines += ["| Section | Rules | Model |", "|---|---|---|"]

        for name in sorted({key.split(".")[0] for key in answered}):
            lines.append(
                f"| {name} | {answered.get(name + '.rules', 0)} | "
                f"{answered.get(name + '.model', 0)} |"
            )

    return lines + [""]


def weakest(results: Sequence[CVResult], limit: int = 10) -> List[Tuple[str, float]]:
    """(anonymous id, core F1) of the CVs the system did worst on, for local use."""

    return sorted(((r.id, core_f1([r])) for r in results), key=lambda item: item[1])[:limit]
