"""
Checks that what the LLM extracted really comes from the CV.

A model can invent a company, or be told by text hidden in the CV to report
one. Name-like fields (role, company, institution, title, ...) must share
most of their words with the source text; a field that does not is dropped.
Dates, lists of bullets and degree levels are normalised by the model, so
they are not checked.
"""

from typing import Any, Dict, Iterable, List, Sequence

from loguru import logger

from app.extraction.section.heading_lexicon import normalise

MIN_OVERLAP = 0.5

# Words shorter than this carry no evidence ("of", "at", "&").
MIN_WORD_LENGTH = 2


def _words(text: str) -> List[str]:
    return [w for w in normalise(text).split() if len(w) >= MIN_WORD_LENGTH]


def is_grounded(value: Any, source: str, min_overlap: float = MIN_OVERLAP) -> bool:
    """True when enough of the value's words appear in the source text."""

    if not isinstance(value, str) or not value.strip():
        return True

    value_words = _words(value)

    if not value_words:
        return True

    source_words = set(_words(source))

    present = sum(1 for word in value_words if word in source_words)

    return present / len(value_words) >= min_overlap


def ground_entries(
    entries: Iterable[Dict[str, Any]],
    fields: Sequence[str],
    source: str,
    label: str,
) -> List[Dict[str, Any]]:
    """
    Sets name-like fields that are not in the source text to None. Returns
    the entries (modified in place) and logs how many values were dropped,
    without logging the values.
    """

    result = list(entries)
    dropped = 0

    for entry in result:
        for field in fields:
            if not is_grounded(entry.get(field), source):
                entry[field] = None
                dropped += 1

    if dropped:
        logger.warning(
            "Dropped {} {} value(s) that do not appear in the resume text.",
            dropped,
            label,
        )

    return result
