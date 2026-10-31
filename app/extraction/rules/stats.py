"""How often the rules answered and how often the model had to be asked."""

import threading
from collections import Counter
from contextvars import ContextVar, Token
from typing import Dict, Optional

_lock = threading.Lock()
_counts: Counter = Counter()

# Counts for the document being processed in this thread, so one CV can be
# told apart from the benchmark totals above.
_document: ContextVar[Optional[Counter]] = ContextVar(
    "extraction_document_counts",
    default=None,
)


def record(section: str, by_rules: bool) -> None:
    key = f"{section}.{'rules' if by_rules else 'model'}"

    with _lock:
        _counts[key] += 1

    current = _document.get()

    if current is not None:
        current[key] += 1


def begin_document() -> Token:
    """Starts counting for one document; pass the token to end_document."""

    return _document.set(Counter())


def end_document(token: Token) -> Dict[str, int]:
    """Stops counting and returns what the document used."""

    counts = _document.get()
    _document.reset(token)

    return dict(counts) if counts is not None else {}


def snapshot() -> Dict[str, int]:
    with _lock:
        return dict(_counts)


def reset() -> None:
    with _lock:
        _counts.clear()
