"""How often the rules answered and how often the model had to be asked."""

import threading
from collections import Counter
from typing import Dict

_lock = threading.Lock()
_counts: Counter = Counter()


def record(section: str, by_rules: bool) -> None:
    with _lock:
        _counts[f"{section}.{'rules' if by_rules else 'model'}"] += 1


def snapshot() -> Dict[str, int]:
    with _lock:
        return dict(_counts)


def reset() -> None:
    with _lock:
        _counts.clear()
