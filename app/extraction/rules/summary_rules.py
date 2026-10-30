"""
The summary section already is the summary: section detection isolated it.
The model was only being asked to copy it, minus anything that is not
introductory text. When the text is plain prose that task needs no model.
"""

from typing import Optional

from app.extraction.section.heading_lexicon import looks_like_contact

MAX_SUMMARY_CHARS = 1500
MAX_SUMMARY_LINES = 12


def parse_summary(text: str) -> Optional[str]:
    """The summary text, or None when the model should look at it."""

    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]

    if not lines or len(lines) > MAX_SUMMARY_LINES:
        return None

    joined = " ".join(lines)

    if len(joined) > MAX_SUMMARY_CHARS or looks_like_contact(joined):
        return None

    # Bullets, dates or many short lines mean this is not one paragraph.
    if any(line[:1] in "-•*▪●" for line in lines):
        return None

    return joined
