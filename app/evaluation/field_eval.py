"""
Field-level scoring of resume extraction against corpus entities.

Section detection (section_eval.py) says whether text reached the right
section. This module asks the next question: did the extractors read the
right facts out of it? The corpus documents record the entities they were
generated from (company, role, school, degree, skills, certificates, name),
so an extraction result can be scored per field without any manual labels.

It works on the dictionary the extraction engine returns and does not run a
model itself, so it can score the LLM extractors, a rule-based baseline or a
future faster path with the same code.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from app.extraction.section.heading_lexicon import normalise

FIELDS = (
    "name",
    "companies",
    "roles",
    "schools",
    "degrees",
    "skills",
    "certifications",
)

# Keys that hold the text of an entity in dictionary items.
_NAME_KEYS = ("name", "title", "skill", "normalized_name", "certification")

# A shorter string that is contained in a longer one only counts as a match
# when it is distinctive enough ("Hanoi" inside "Hanoi University" does not).
MIN_CONTAINED_CHARS = 5
MIN_CONTAINED_WORDS = 2


@dataclass
class FieldScore:
    precision: float
    recall: float
    f1: float
    expected: int
    found: int


def _text(item: Any, keys: Sequence[str] = _NAME_KEYS) -> str:
    if isinstance(item, str):
        return item

    if isinstance(item, Mapping):
        for key in keys:
            value = item.get(key)

            if isinstance(value, str) and value.strip():
                return value

    return ""


def _values(items: Any, *keys: str) -> List[str]:
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes)):
        return []

    return [text for item in items if (text := _text(item, keys or _NAME_KEYS))]


def entities_from_extraction(extracted: Mapping[str, Any]) -> Dict[str, List[str]]:
    """Maps the extraction engine's output to the corpus entity fields."""

    personal = extracted.get("personal_info") or {}
    experience = extracted.get("experience") or []
    education = extracted.get("education") or []

    degrees: List[str] = []

    for entry in education:
        if not isinstance(entry, Mapping):
            continue

        value = entry.get("degree") or entry.get("degree_level") or entry.get("field_of_study")

        if isinstance(value, str):
            degrees.append(value)
        elif isinstance(value, list):
            degrees.extend(v for v in value if isinstance(v, str))

    return {
        "name": [personal["full_name"]] if isinstance(personal, Mapping) and personal.get("full_name") else [],
        "companies": _values(experience, "company"),
        "roles": _values(experience, "role"),
        "schools": _values(education, "institution"),
        "degrees": degrees,
        "skills": _values(extracted.get("skills")),
        "certifications": _values(extracted.get("certifications")),
    }


def same_entity(expected: str, found: str) -> bool:
    a, b = normalise(expected), normalise(found)

    if not a or not b:
        return False

    if a == b:
        return True

    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)

    distinctive = (
        len(shorter) >= MIN_CONTAINED_CHARS
        and len(shorter.split()) >= MIN_CONTAINED_WORDS
    )

    return distinctive and f" {shorter} " in f" {longer} "


def _degree_words(text: str) -> set:
    """The words of the text that name a kind of degree (bachelor, master, licence ...)."""

    from app.extraction.rules.vocabulary import get_vocabulary

    return set(normalise(text).split()) & get_vocabulary().degrees.words


def same_degree(expected: str, found: str) -> bool:
    """
    Degrees are written at different lengths: "Bachelor" and "Bachelor of
    Science in Computer Science" name the same degree. Two values match when
    they are the same entity or share a word that names a kind of degree.
    """

    return same_entity(expected, found) or bool(
        _degree_words(expected) & _degree_words(found)
    )


def _distinct(values: Sequence[str]) -> List[str]:
    """The values without repeats, comparing them as same_entity does."""

    return list({normalise(value): value for value in values if normalise(value)}.values())


def score_fields(
    expected: Mapping[str, Sequence[str]],
    extracted: Mapping[str, Sequence[str]],
) -> Dict[str, FieldScore]:
    """Precision, recall and F1 per field for one document."""

    scores: Dict[str, FieldScore] = {}

    for name in FIELDS:
        wanted = _distinct(expected.get(name, []))
        got = _distinct(extracted.get(name, []))

        matches = same_degree if name == "degrees" else same_entity

        hits = sum(any(matches(w, g) for g in got) for w in wanted)
        correct = sum(any(matches(w, g) for w in wanted) for g in got)

        precision = correct / len(got) if got else 0.0
        recall = hits / len(wanted) if wanted else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        scores[name] = FieldScore(precision, recall, f1, len(wanted), len(got))

    return scores


def aggregate_fields(
    per_document: Iterable[Mapping[str, FieldScore]]
) -> Dict[str, FieldScore]:
    """Micro-averaged scores over documents (counts are summed, not averaged)."""

    totals: Dict[str, List[float]] = {name: [0.0, 0.0, 0.0, 0.0] for name in FIELDS}

    for scores in per_document:
        for name, score in scores.items():
            totals[name][0] += score.recall * score.expected   # hits
            totals[name][1] += score.precision * score.found   # correct
            totals[name][2] += score.expected
            totals[name][3] += score.found

    result: Dict[str, FieldScore] = {}

    for name, (hits, correct, expected, found) in totals.items():
        precision = correct / found if found else 0.0
        recall = hits / expected if expected else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        result[name] = FieldScore(precision, recall, f1, int(expected), int(found))

    return result


def field_table(scores: Mapping[str, FieldScore]) -> str:
    rows = [
        "| Field | Precision | Recall | F1 | Expected | Found |",
        "|---|---|---|---|---|---|",
    ]

    for name in FIELDS:
        score = scores[name]
        rows.append(
            f"| {name} | {score.precision:.3f} | {score.recall:.3f} | "
            f"{score.f1:.3f} | {score.expected} | {score.found} |"
        )

    return "\n".join(rows)
