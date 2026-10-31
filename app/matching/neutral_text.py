"""
Removes from a profile's text the words that say who the person is, not what
they can do, before the text is embedded: gendered pronouns and titles, and
the person's own name.

An embedding model reads every word. Measured with the counterfactual audit
(docs/evaluation/fairness.md), a sentence that differs only by "She" or "He",
or a summary that starts with a name, changes the score and the share of
candidates selected. Names and pronouns have no place in a job match, so they
are taken out of the text that is compared, not left for the model to ignore.

This does not remove everything: group memberships ("women in engineering
society"), a photograph, a date of birth or the language of the CV can still
carry the information, and some of those are not safe to delete because they
also say something about skills.
"""

import re
from typing import Iterable, Optional

# Vietnamese pronouns are two words; they are replaced before the English ones.
_PHRASES = {
    "anh ấy": "họ",
    "chị ấy": "họ",
    "cô ấy": "họ",
    "ông ấy": "họ",
    "bà ấy": "họ",
}

_WORDS = {
    "he": "they",
    "she": "they",
    "him": "them",
    "her": "their",
    "his": "their",
    "hers": "theirs",
    "himself": "themselves",
    "herself": "themselves",
}

_TITLES = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Mx|Sir|Madam)\b\.?\s*", re.IGNORECASE)

_PHRASE_PATTERN = re.compile(
    "|".join(re.escape(phrase) for phrase in _PHRASES), re.IGNORECASE
)
_WORD_PATTERN = re.compile(
    r"\b(" + "|".join(_WORDS) + r")\b", re.IGNORECASE
)

MIN_NAME_PART = 3


def _replace_word(match: "re.Match[str]") -> str:
    word = match.group(0)

    # "SHE" in capitals is an acronym (Safety, Health and Environment).
    if len(word) > 1 and word.isupper():
        return word

    return _WORDS[word.lower()]


def name_parts(full_name: Optional[str]) -> Iterable[str]:
    """The full name and its parts that are long enough to be a name and not a letter."""

    if not full_name or not full_name.strip():
        return []

    full = " ".join(full_name.split())
    parts = [part for part in re.split(r"[\s,]+", full) if len(part) >= MIN_NAME_PART]

    return [full, *parts]


def neutralise(text: str, full_name: Optional[str] = None) -> str:
    """The text without gendered pronouns and titles and without the person's name."""

    if not text:
        return text

    for name in name_parts(full_name):
        text = re.sub(
            r"(?<!\w)" + re.escape(name) + r"(?!\w)",
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = _PHRASE_PATTERN.sub(lambda m: _PHRASES[m.group(0).lower()], text)
    text = _TITLES.sub(" ", text)
    text = _WORD_PATTERN.sub(_replace_word, text)

    return " ".join(text.split())
