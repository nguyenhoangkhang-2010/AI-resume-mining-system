"""
The word lists the rule parsers rely on, kept as data.

Job-title words, employer words, school and degree words, month names, the
words for "until now" and place names are language knowledge, not program
logic. They live in JSON files next to this module (one per language) and in
an optional extra directory (`VOCABULARY_DIR`), and all files found are merged.
Supporting another language, or a field's own jargon, means adding a file; no
code changes.

Entries can be written naturally (with accents and capitals); they are
normalised when loaded, the same way the text they are compared with is.

File format (every key except "language" is optional):

    {
      "language": "en",
      "roles":        {"words": [...], "phrases": [...]},
      "companies":    {"words": [...], "phrases": [...]},
      "company_suffixes": ["inc", "ltd"],
      "institutions": {"words": [...], "phrases": [...]},
      "degrees":      {"words": [...], "phrases": [...]},
      "places":       {"words": [...], "phrases": [...]},
      "months": [...], "present": [...], "range_words": [...],
      "headings": {"experience": [...], "education": [...], ...},
      "filler_words": [...]
    }

"headings" lists the section headings of the language (see HEADING_SECTIONS
for the section names) and "filler_words" the small words that may surround a
heading ("and", "de", "und").

A "word" matches one whole word of the text; a "phrase" matches several
consecutive words.
"""

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from app.core.config.settings import settings
from app.extraction.section.heading_lexicon import normalise

BUILTIN_DIRECTORY = Path(__file__).parent / "vocabulary"

TERM_GROUPS = ("roles", "companies", "institutions", "degrees", "places")
LIST_KEYS = ("months", "present", "range_words", "company_suffixes")
HEADING_SECTIONS = (
    "personal_info",
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "other",
)
KNOWN_KEYS = {"language", "headings", "filler_words", *TERM_GROUPS, *LIST_KEYS}


@dataclass(frozen=True)
class Terms:
    words: FrozenSet[str] = frozenset()
    phrases: Tuple[str, ...] = ()

    def count(self, text: str) -> int:
        """How many different words and phrases of this group the text contains."""

        normalised = normalise(text)
        tokens = set(normalised.split())
        padded = f" {normalised} "

        return len(self.words & tokens) + sum(
            1 for phrase in self.phrases if f" {phrase} " in padded
        )


    def covers(self, text: str) -> bool:
        """True when the text is made of nothing but words and phrases of this group."""

        normalised = normalise(text)

        if not normalised:
            return False

        padded = f" {normalised} "

        for phrase in sorted(self.phrases, key=len, reverse=True):
            padded = padded.replace(f" {phrase} ", " ")

        return all(token in self.words for token in padded.split())


@dataclass(frozen=True)
class Vocabulary:
    roles: Terms = Terms()
    companies: Terms = Terms()
    institutions: Terms = Terms()
    degrees: Terms = Terms()
    places: Terms = Terms()
    company_suffixes: FrozenSet[str] = frozenset()
    months: Tuple[str, ...] = ()
    present: Tuple[str, ...] = ()
    range_words: Tuple[str, ...] = ()
    # (section, phrases) pairs; a tuple, because the vocabulary is hashed.
    headings: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()
    filler_words: FrozenSet[str] = frozenset()
    languages: Tuple[str, ...] = field(default_factory=tuple)


def _strings(value: Any, where: str) -> List[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{where}: expected a list of non-empty strings")

    return [item.strip() for item in value]


def read_file(path: Path) -> Dict[str, Any]:
    """One vocabulary file, checked. Raises ValueError naming the file."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path.name}: cannot be read as JSON ({exc})") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a JSON object")

    unknown = sorted(set(data) - KNOWN_KEYS)

    if unknown:
        raise ValueError(f"{path.name}: unknown keys {unknown}")

    for group in TERM_GROUPS:
        if group in data:
            terms = data[group]

            if not isinstance(terms, dict) or set(terms) - {"words", "phrases"}:
                raise ValueError(f"{path.name}: '{group}' needs 'words' and/or 'phrases'")

            for kind in terms:
                _strings(terms[kind], f"{path.name}: {group}.{kind}")

    for key in (*LIST_KEYS, "filler_words"):
        if key in data:
            _strings(data[key], f"{path.name}: {key}")

    if "headings" in data:
        headings = data["headings"]

        if not isinstance(headings, dict):
            raise ValueError(f"{path.name}: 'headings' needs a section name for each key")

        unknown_sections = sorted(set(headings) - set(HEADING_SECTIONS))

        if unknown_sections:
            raise ValueError(
                f"{path.name}: unknown sections {unknown_sections} in 'headings' "
                f"(use {list(HEADING_SECTIONS)})"
            )

        for section, phrases in headings.items():
            _strings(phrases, f"{path.name}: headings.{section}")

    return data


def build(files: Sequence[Dict[str, Any]]) -> Vocabulary:
    """Merges the contents of several vocabulary files."""

    words: Dict[str, set] = {group: set() for group in TERM_GROUPS}
    phrases: Dict[str, List[str]] = {group: [] for group in TERM_GROUPS}
    lists: Dict[str, List[str]] = {key: [] for key in LIST_KEYS}
    headings: Dict[str, List[str]] = {}
    fillers: set = set()
    languages: List[str] = []

    for data in files:
        if data.get("language"):
            languages.append(str(data["language"]))

        for group in TERM_GROUPS:
            terms = data.get(group) or {}

            for entry in terms.get("words", []):
                normalised = normalise(entry)

                if normalised:
                    words[group].add(normalised)

            for entry in terms.get("phrases", []):
                normalised = normalise(entry)

                if normalised and normalised not in phrases[group]:
                    phrases[group].append(normalised)

        for section, entries in (data.get("headings") or {}).items():
            known = headings.setdefault(section, [])

            for entry in entries:
                normalised = normalise(entry)

                if normalised and normalised not in known:
                    known.append(normalised)

        for entry in data.get("filler_words") or []:
            if normalise(entry):
                fillers.add(normalise(entry))

        for key in LIST_KEYS:
            for entry in data.get(key) or []:
                if entry.strip() and entry.strip().casefold() not in lists[key]:
                    lists[key].append(entry.strip().casefold())

    return Vocabulary(
        roles=Terms(frozenset(words["roles"]), tuple(phrases["roles"])),
        companies=Terms(frozenset(words["companies"]), tuple(phrases["companies"])),
        institutions=Terms(frozenset(words["institutions"]), tuple(phrases["institutions"])),
        degrees=Terms(frozenset(words["degrees"]), tuple(phrases["degrees"])),
        places=Terms(frozenset(words["places"]), tuple(phrases["places"])),
        company_suffixes=frozenset(normalise(s) for s in lists["company_suffixes"]),
        months=tuple(lists["months"]),
        present=tuple(lists["present"]),
        range_words=tuple(lists["range_words"]),
        headings=tuple((section, tuple(items)) for section, items in headings.items()),
        filler_words=frozenset(fillers),
        languages=tuple(languages),
    )


def load_vocabulary(directories: Iterable[Path]) -> Vocabulary:
    """Every *.json file of the directories, merged (names sorted, so the result is stable)."""

    files: List[Dict[str, Any]] = []

    for directory in directories:
        if directory.is_dir():
            files.extend(read_file(path) for path in sorted(directory.glob("*.json")))

    return build(files)


@lru_cache(maxsize=4)
def _cached(extra: Optional[str]) -> Vocabulary:
    directories = [BUILTIN_DIRECTORY]

    if extra:
        directories.append(Path(extra))

    return load_vocabulary(directories)


def get_vocabulary() -> Vocabulary:
    """The vocabulary in use: the built-in files plus `VOCABULARY_DIR`, if set."""

    return _cached(getattr(settings, "VOCABULARY_DIR", None) or None)


def clear_cache() -> None:
    _cached.cache_clear()

    # The heading lexicon keeps what it read from the vocabulary.
    from app.extraction.section import heading_lexicon

    heading_lexicon.clear_cache()
