"""
Defences against prompt injection in resume text.

Resume text is untrusted: anyone can put "ignore the previous instructions"
or a fake chat marker in a CV. Three layers are used:

- sanitize: remove chat-control tokens and forged section delimiters from the
  text before it goes into a prompt, so the text cannot close the
  instruction block or pretend the answer has started;
- detect: report likely injection attempts so a recruiter can look at them;
- ground (see app.extraction.grounding): fields the model returns must come
  from the CV text.

None of this makes a language model injection-proof. It removes the cheapest
attacks and makes the rest visible.
"""

import re
from typing import List

# Markers of the chat formats of Mistral/Llama, ChatML and similar. A CV has
# no reason to contain them.
_CONTROL_TOKENS = re.compile(
    r"\[/?INST\]"
    r"|<<\s*/?\s*SYS\s*>>"
    r"|</?s>"
    r"|<\|[^|>\n]{1,40}\|>"
    r"|<\s*/?\s*(?:system|assistant|user)\s*>",
    re.IGNORECASE,
)

# Characters that are invisible or only steer rendering.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁠﻿]")

# Our own prompt delimiters, written as "--- Input Text ---" / "--- Output ---".
_DELIMITER_LINE = re.compile(
    r"^.*-{3,}\s*(?:input text|output)\s*-{3,}.*$",
    re.IGNORECASE | re.MULTILINE,
)

_INJECTION_PATTERNS = {
    "ignore_instructions": re.compile(
        r"\b(?:ignore|disregard|forget|override)\b.{0,40}"
        r"\b(?:previous|prior|above|earlier|all|any|your)\b.{0,30}"
        r"\b(?:instructions?|prompts?|rules?|context|directions?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    "new_instructions": re.compile(
        r"\b(?:new|updated|real)\s+instructions?\s*:", re.IGNORECASE
    ),
    "role_change": re.compile(
        r"\b(?:you are now|from now on,? you|act as (?:an?|the)|pretend (?:to be|you are))\b",
        re.IGNORECASE,
    ),
    "prompt_leak": re.compile(
        r"\b(?:reveal|show|print|repeat|output)\b.{0,30}"
        r"\b(?:system prompt|your prompt|your instructions|the prompt)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    "score_manipulation": re.compile(
        r"\b(?:rate|score|rank|recommend)\b.{0,40}"
        r"\b(?:this (?:candidate|resume|cv)|me)\b.{0,40}"
        r"\b(?:highest|10/10|100|top|perfect|best)\b",
        re.IGNORECASE | re.DOTALL,
    ),
}


def sanitize_untrusted_text(text: str) -> str:
    """Removes chat-control tokens, control characters and forged delimiters."""

    text = _CONTROL_CHARS.sub("", text)
    text = _CONTROL_TOKENS.sub(" ", text)
    text = _DELIMITER_LINE.sub("[line removed]", text)

    return text


def strip_control_tokens(prompt: str) -> str:
    """For a finished prompt: only the chat-control tokens are removed."""

    return _CONTROL_TOKENS.sub(" ", prompt)


def detect_prompt_injection(text: str) -> List[str]:
    """
    Names of the injection patterns found in the text. Chat-control tokens
    count as one; the matched text itself is never returned.
    """

    found = [
        name for name, pattern in _INJECTION_PATTERNS.items() if pattern.search(text)
    ]

    if _CONTROL_TOKENS.search(text):
        found.append("chat_control_tokens")

    return found
