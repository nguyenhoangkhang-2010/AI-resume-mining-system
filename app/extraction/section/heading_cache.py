"""
Remembers which section an unfamiliar heading introduces.

Asking the language model what "Clinical Experience" means costs seconds,
but the answer never changes and the same headings come back in every CV of
a field. Answers are stored by normalised heading text (case, accents and
punctuation ignored), so each distinct heading is classified once, and
kept in a small JSON file so that the answer survives a restart.
"""

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from app.extraction.section.heading_lexicon import normalise

# Stops a stream of junk "headings" from growing the file without limit.
MAX_ENTRIES = 5000


class HeadingCache:

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else None
        self._entries: Dict[str, str] = {}
        self._lock = threading.Lock()

        if self.path is not None:
            self._load()

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, heading: str) -> Optional[str]:
        return self._entries.get(normalise(heading))

    def put(self, heading: str, section: str) -> None:
        key = normalise(heading)

        if not key:
            return

        with self._lock:
            if key not in self._entries and len(self._entries) >= MAX_ENTRIES:
                return

            self._entries[key] = section
            self._save()

    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.path is None or not self.path.is_file():
            return

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.warning("Heading cache could not be read; starting empty.")
            return

        if isinstance(data, dict):
            self._entries = {
                str(key): str(value)
                for key, value in data.items()
                if isinstance(value, str)
            }

    def _save(self) -> None:
        if self.path is None:
            return

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)

            # Write to a temporary file first so a crash cannot leave a
            # half-written cache behind.
            handle, temporary = tempfile.mkstemp(
                dir=self.path.parent, suffix=".tmp"
            )

            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(self._entries, stream, ensure_ascii=False, indent=0)

            os.replace(temporary, self.path)
        except OSError as exc:
            logger.warning("Heading cache could not be saved: {}", exc)
