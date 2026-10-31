"""
How far one extracted CV can be trusted.

The score is not a probability. It combines what the pipeline can observe
about its own work: how complete the result is, how the sections were found
(a heading the CV spells out versus a model's guess), who answered each
extractor (rules versus model), whether the text came from OCR and whether
the entries it returned have their key fields. `scripts/evaluate_confidence.py`
checks how well the score follows the real accuracy of the extraction.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.extraction.rules.dates import find_range

_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")

LOW = "low"
MEDIUM = "medium"
HIGH = "high"

HIGH_FROM = 0.9
MEDIUM_FROM = 0.5

WEIGHTS = {
    "completeness": 0.35,
    "structure": 0.25,
    "extraction": 0.20,
    "fields": 0.20,
}

# How much a way of finding a section is worth, before the classifier's own
# confidence is applied where it has one.
SECTION_METHOD_TRUST = {
    "contact_header": 1.0,
    "heading_words": 1.0,
    "heading_style": 0.9,
    "continued": 0.8,
    "column": 0.7,
    "semantic": 0.7,
    "model_guess": 0.5,
}

CORE_SECTIONS = ("experience", "education", "skills")

# An extractor answered by the model is less certain than one answered by
# the rules, which only accept what has the expected shape.
MODEL_ANSWER_TRUST = 0.7

OCR_FACTOR = 0.85

MIN_USEFUL_CHARS = 400


@dataclass
class Confidence:
    score: float
    level: str
    components: Dict[str, float] = field(default_factory=dict)
    sections: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "components": self.components,
            "sections": self.sections,
            "reasons": self.reasons,
        }


def level_of(score: float) -> str:
    if score >= HIGH_FROM:
        return HIGH

    if score >= MEDIUM_FROM:
        return MEDIUM

    return LOW


def assess_confidence(extracted: Dict[str, Any]) -> Confidence:
    """Scores one pipeline result (the output of `process_pdf`)."""

    signals = extracted.get("signals") or {}
    reasons: List[str] = []

    completeness = _completeness(extracted, reasons)

    section_scores = _section_scores(signals.get("sections") or [])
    structure = _structure(section_scores, extracted, reasons)

    extraction = _extraction(signals.get("methods") or {}, extracted, reasons)

    fields = _fields(extracted, reasons)

    components = {
        "completeness": completeness,
        "structure": structure,
        "extraction": extraction,
        "fields": fields,
    }

    score = sum(WEIGHTS[name] * value for name, value in components.items())

    if signals.get("ocr_pages"):
        score *= OCR_FACTOR
        reasons.append("read_by_ocr")

    if len(extracted.get("raw_text") or "") < MIN_USEFUL_CHARS:
        score *= 0.8
        reasons.append("very_little_text")

    score = round(max(0.0, min(1.0, score)), 3)

    return Confidence(
        score=score,
        level=level_of(score),
        components={name: round(value, 3) for name, value in components.items()},
        sections={name: round(value, 3) for name, value in section_scores.items()},
        reasons=reasons,
    )


def _completeness(extracted: Dict[str, Any], reasons: List[str]) -> float:
    personal = extracted.get("personal_info") or {}

    checks = {
        "name": bool(personal.get("full_name")),
        "contact": bool(personal.get("email") or personal.get("phone")),
        "experience": bool(extracted.get("experience")),
        "education": bool(extracted.get("education")),
        "skills": bool(extracted.get("skills")),
    }

    weights = {
        "name": 0.15,
        "contact": 0.15,
        "experience": 0.30,
        "education": 0.20,
        "skills": 0.20,
    }

    for name, present in checks.items():
        if not present:
            reasons.append(f"{name}_missing")

    return sum(weights[name] for name, present in checks.items() if present)


def _section_scores(provenance: List[str]) -> Dict[str, float]:
    """The best trust among the segments that were read as each section."""

    scores: Dict[str, float] = {}

    for entry in provenance:
        parts = entry.split(":")

        if len(parts) != 3:
            continue

        name, how, raw_confidence = parts

        try:
            classifier_confidence = float(raw_confidence)
        except ValueError:
            continue

        trust = SECTION_METHOD_TRUST.get(how, 0.5)

        # Only the guessing methods carry a confidence worth applying.
        if how in {"semantic", "model_guess"}:
            trust *= max(0.0, min(1.0, classifier_confidence))

        scores[name] = max(scores.get(name, 0.0), trust)

    return scores


def _structure(
    section_scores: Dict[str, float],
    extracted: Dict[str, Any],
    reasons: List[str],
) -> float:
    """How surely the sections that matter were found."""

    values: List[float] = []

    for name in CORE_SECTIONS:
        if not extracted.get(name):
            # Nothing came out of it; completeness already counts that.
            continue

        trust = section_scores.get(name)

        if trust is None:
            # Skills are collected from the whole text and need no section.
            if name == "skills":
                continue

            values.append(0.3)
            reasons.append(f"{name}_without_section")
            continue

        if trust < 0.6:
            reasons.append(f"{name}_section_guessed")

        values.append(trust)

    if not values:
        return 0.0

    return sum(values) / len(values)


def _extraction(
    methods: Dict[str, int],
    extracted: Dict[str, Any],
    reasons: List[str],
) -> float:
    """Share of the extractors that were answered by the rules."""

    values: List[float] = []

    for name in ("experience", "education"):
        if not extracted.get(name):
            continue

        rules = methods.get(f"{name}.rules", 0)
        model = methods.get(f"{name}.model", 0)

        if rules + model == 0:
            values.append(MODEL_ANSWER_TRUST)
            continue

        share = rules / (rules + model)
        values.append(share + (1.0 - share) * MODEL_ANSWER_TRUST)

        if share == 0.0:
            reasons.append(f"{name}_read_by_model")

    if not values:
        return 0.0

    return sum(values) / len(values)


def _fields(extracted: Dict[str, Any], reasons: List[str]) -> float:
    """
    Whether the entries that were returned look right: they carry their key
    fields, their text is the size of a name (not a sentence), and the dates
    that appear in the CV were matched to entries.
    """

    experience = _entries(extracted.get("experience"))
    education = _entries(extracted.get("education"))

    values: List[float] = []

    if experience:
        values.append(
            _share(
                experience,
                lambda entry: bool(entry.get("company") or entry.get("role")),
            )
        )
        dated = _share(experience, _has_date)
        values.append(dated)

        if dated < 0.5:
            reasons.append("experience_without_dates")

        values.append(
            _share(
                experience,
                lambda entry: _plausible(entry.get("company"))
                and _plausible(entry.get("role")),
            )
        )

    if education:
        values.append(
            _share(
                education,
                lambda entry: bool(entry.get("institution")),
            )
        )
        values.append(
            _share(education, lambda entry: _plausible(entry.get("institution")))
        )

    coverage = _date_coverage(extracted, experience + education)

    if coverage is not None:
        values.append(coverage)

        if coverage < DATE_COVERAGE_WARNING:
            reasons.append("dates_not_matched_to_entries")

    if not values:
        return 0.0

    return sum(values) / len(values)


DATE_KEYS = ("start_date", "end_date", "start_year", "end_year", "duration")

# A name of an employer, a school or a job title is short. A long value is
# usually a sentence or a whole block read as one field.
MAX_NAME_WORDS = 10

DATE_COVERAGE_WARNING = 0.6


def _entries(value: Any) -> List[Dict[str, Any]]:
    return [entry for entry in (value or []) if isinstance(entry, dict)]


def _has_date(entry: Dict[str, Any]) -> bool:
    return any(entry.get(key) for key in DATE_KEYS)


def _plausible(value: Any) -> bool:
    """Empty counts as plausible: a missing value is judged elsewhere."""

    if not value:
        return True

    if not isinstance(value, str):
        return False

    return len(value.split()) <= MAX_NAME_WORDS and not _YEAR.search(value)


def _date_coverage(
    extracted: Dict[str, Any],
    entries: List[Dict[str, Any]],
) -> Optional[float]:
    """
    Date ranges written in the CV against entries that have dates. A CV with
    four ranges and one dated job lost jobs. None when the text has no range.
    """

    ranges = sum(
        1
        for line in (extracted.get("raw_text") or "").splitlines()
        if find_range(line) is not None
    )

    if ranges == 0:
        return None

    return min(1.0, sum(1 for entry in entries if _has_date(entry)) / ranges)


def _share(entries: List[Dict[str, Any]], test) -> float:
    return sum(1 for entry in entries if test(entry)) / len(entries)
