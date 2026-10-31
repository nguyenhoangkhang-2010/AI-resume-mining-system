"""
Labels for a private set of real CVs.

Real CVs contain personal data, so neither the PDFs nor the labels are kept
in the repository: they live in a git-ignored folder on the machine of the
person who owns them. What may be published is only aggregate numbers.

A label file says which sections a CV has and which entities it contains
(name, companies, roles, schools, degrees, skills, certificates). It starts
as a draft made from what the system extracted, which a person then corrects
against the PDF and marks as reviewed. Only reviewed files are scored.

Drafting from the system's own output is quicker than labelling from scratch
but anchors the labeller towards what the system already says; see
docs/evaluation/real_cv_README.md.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from app.evaluation.field_eval import FIELDS

DRAFT = "draft"
REVIEWED = "reviewed"

SECTIONS = (
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
)

TAG_KEYS = ("language", "industry", "layout", "pages")

# Groups smaller than this are not reported separately: with one or two CVs a
# "group result" describes (and can identify) a single person.
MIN_GROUP = 3

INDEX_NAME = "index.json"


@dataclass
class LabelFile:
    id: str
    file: str
    status: str = DRAFT
    tags: Dict[str, str] = field(default_factory=dict)
    sections_present: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    notes: str = ""

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file": self.file,
            "status": self.status,
            "tags": self.tags,
            "sections_present": self.sections_present,
            "entities": {name: self.entities.get(name, []) for name in FIELDS},
            "notes": self.notes,
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> "LabelFile":
        entities = data.get("entities") or {}

        return cls(
            id=str(data.get("id", "")),
            file=str(data.get("file", "")),
            status=str(data.get("status", DRAFT)),
            tags={str(k): str(v) for k, v in (data.get("tags") or {}).items()},
            sections_present=[str(s) for s in data.get("sections_present") or []],
            entities={
                str(name): [str(v) for v in values]
                for name, values in entities.items()
                if isinstance(values, list)
            },
            notes=str(data.get("notes", "")),
        )


def save_label(directory: Path, label: LabelFile) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{label.id}.json"
    path.write_text(
        json.dumps(label.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return path


def load_labels(directory: Path) -> List[LabelFile]:
    labels = []

    for path in sorted(Path(directory).glob("*.json")):
        if path.name == INDEX_NAME or path.name.startswith("picked"):
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            labels.append(LabelFile(id=path.stem, file="", status="unreadable"))
            continue

        label = LabelFile.from_json(data)
        label.id = label.id or path.stem
        labels.append(label)

    return labels


def validate(labels: Sequence[LabelFile]) -> List[str]:
    """Problems found in the label files, naming only anonymous ids."""

    problems: List[str] = []
    seen: Dict[str, str] = {}

    for label in labels:
        if label.status == "unreadable":
            problems.append(f"{label.id}: file is not valid JSON")
            continue

        if label.status not in (DRAFT, REVIEWED):
            problems.append(f"{label.id}: status must be 'draft' or 'reviewed'")

        if not label.file:
            problems.append(f"{label.id}: no PDF file name")
        elif label.file in seen:
            problems.append(f"{label.id}: same PDF as {seen[label.file]}")
        else:
            seen[label.file] = label.id

        unknown = sorted(set(label.sections_present) - set(SECTIONS))

        if unknown:
            problems.append(f"{label.id}: unknown sections {unknown}")

        extra = sorted(set(label.entities) - set(FIELDS))

        if extra:
            problems.append(f"{label.id}: unknown entity fields {extra}")

        if label.status == REVIEWED and not any(label.entities.values()):
            problems.append(f"{label.id}: reviewed but has no entities at all")

    return problems


# ----------------------------------------------------------------- drafting


def present_sections(sections: Mapping[str, Sequence[str]]) -> List[str]:
    """The scored sections the detector found text for."""

    return [
        name
        for name in SECTIONS
        if any(chunk.strip() for chunk in sections.get(name, []))
    ]


def guess_language(text: str) -> str:
    """
    "vi" for text with Vietnamese letters, "en" for plain Latin text, "other"
    when a large share of the letters are not Latin. A starting point for a
    tag a person will check.
    """

    letters = [c for c in text if c.isalpha()]

    if not letters:
        return "other"

    non_latin = sum(
        1 for c in letters if "LATIN" not in unicodedata.name(c, "")
    )

    if non_latin / len(letters) > 0.2:
        return "other"

    vietnamese = sum(1 for c in letters if c in _VIETNAMESE_LETTERS)

    return "vi" if vietnamese / len(letters) > 0.02 else "en"


_VIETNAMESE_LETTERS = frozenset(
    "ăâđêôơưĂÂĐÊÔƠƯ"
    "ạảãàáậẩẫầấặẳẵằắẹẻẽèéệểễềếịỉĩìíọỏõòóộổỗồốợởỡờớụủũùúựửữừứỵỷỹỳý"
    "ẠẢÃÀÁẬẨẪẦẤẶẲẴẰẮẸẺẼÈÉỆỂỄỀẾỊỈĨÌÍỌỎÕÒÓỘỔỖỒỐỢỞỠỜỚỤỦŨÙÚỰỬỮỪỨỴỶỸỲÝ"
)


def draft_label(
    cv_id: str,
    file_name: str,
    extracted: Mapping[str, Any],
    sections: Mapping[str, Sequence[str]],
    tags: Mapping[str, str],
) -> LabelFile:
    """A label made from what the system extracted, for a person to correct."""

    from app.evaluation.field_eval import entities_from_extraction

    return LabelFile(
        id=cv_id,
        file=file_name,
        status=DRAFT,
        tags=dict(tags),
        sections_present=present_sections(sections),
        entities=entities_from_extraction(extracted),
        notes="Correct against the PDF, then set status to 'reviewed'.",
    )


# ------------------------------------------------------------- picking CVs


@dataclass
class Candidate:
    name: str
    pages: int
    columns: int
    language: str
    chars: int
    text: str = ""


def _shingles(text: str, size: int = 5) -> set:
    words = re.findall(r"\w+", text.casefold())

    if len(words) < size:
        return {" ".join(words)} if words else set()

    return {" ".join(words[i: i + size]) for i in range(len(words) - size + 1)}


def similarity(first: str, second: str) -> float:
    """Jaccard overlap of five-word shingles: 1.0 for the same text."""

    a, b = _shingles(first), _shingles(second)

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b)


def near_duplicate_groups(
    candidates: Sequence[Candidate], threshold: float = 0.5
) -> List[List[int]]:
    """Indexes of candidates grouped by text that is mostly the same."""

    groups: List[List[int]] = []

    for index, candidate in enumerate(candidates):
        for group in groups:
            if similarity(candidates[group[0]].text, candidate.text) >= threshold:
                group.append(index)
                break
        else:
            groups.append([index])

    return groups


def _distance(a: Candidate, b: Candidate) -> float:
    return (
        (a.language != b.language) * 2.0
        + (a.columns != b.columns) * 1.5
        + abs(min(a.pages, 4) - min(b.pages, 4)) * 0.5
        + abs(_length_bucket(a.chars) - _length_bucket(b.chars)) * 0.5
    )


def _length_bucket(chars: int) -> int:
    for bucket, limit in enumerate((1500, 3000, 6000, 12000)):
        if chars < limit:
            return bucket

    return 4


def pick_diverse(
    candidates: Sequence[Candidate], count: int, per_template: int = 2
) -> List[Candidate]:
    """
    A varied subset: at most `per_template` CVs from any group of
    near-identical texts (a template used many times), then the CV farthest
    from those already chosen in language, columns, pages and length.
    """

    pool: List[Candidate] = []

    for group in near_duplicate_groups(candidates):
        pool.extend(candidates[i] for i in group[:per_template])

    if len(pool) <= count:
        return pool

    chosen = [pool[0]]
    remaining = pool[1:]

    while remaining and len(chosen) < count:
        best = max(
            remaining,
            key=lambda c: (min(_distance(c, p) for p in chosen), c.name),
        )
        chosen.append(best)
        remaining.remove(best)

    return chosen


def summarize_candidates(candidates: Iterable[Candidate]) -> Dict[str, Dict[str, int]]:
    """Counts by language, columns and pages (no file names)."""

    counts: Dict[str, Dict[str, int]] = {"language": {}, "columns": {}, "pages": {}}

    for candidate in candidates:
        for key, value in (
            ("language", candidate.language),
            ("columns", str(candidate.columns)),
            ("pages", str(min(candidate.pages, 4))),
        ):
            counts[key][value] = counts[key].get(value, 0) + 1

    return counts


def optional_float(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.3f}"
