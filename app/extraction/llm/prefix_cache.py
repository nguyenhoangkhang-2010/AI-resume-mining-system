"""
Keeps the model's state after it has read a prompt's fixed instructions.

Every extraction prompt is a block of instructions (hundreds of tokens, the
same for every resume) followed by the resume text. A CPU reads about
twenty tokens a second, so re-reading the instructions for every resume
costs tens of seconds per call. The attention state after the instructions
depends only on the instructions, so it is computed once per distinct
instruction text, kept in memory, and restored before each call that starts
with the same instructions.

Reuse never changes the answer: the restored state is exactly what reading
the instructions again would produce, and if the prompt's tokens do not
start with the cached tokens the cache is simply not used.
"""

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, List

from loguru import logger

# Rough size of the attention state per token for a 7B model with grouped
# queries; only used when the library does not report a size.
FALLBACK_BYTES_PER_TOKEN = 140_000


@dataclass
class _Entry:
    tokens: List[int]
    state: Any
    size: int


class PrefixCache:

    def __init__(self, capacity_bytes: int) -> None:
        self.capacity = capacity_bytes
        self._entries: "OrderedDict[str, _Entry]" = OrderedDict()
        self.hits = 0
        self.misses = 0

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def size(self) -> int:
        return sum(entry.size for entry in self._entries.values())

    def prepare(self, llama: Any, instructions: str, prompt: str) -> bool:
        """
        Leaves `llama` having read `instructions`. Returns False when the
        cache cannot be used for this prompt (the caller then reads the whole
        prompt as usual).
        """

        tokens = self._tokenize(llama, instructions)

        if not self._is_prefix(tokens, self._tokenize(llama, prompt)):
            return False

        key = hashlib.sha256(instructions.encode("utf-8")).hexdigest()
        entry = self._entries.get(key)

        if entry is None:
            self.misses += 1

            llama.reset()
            llama.eval(tokens)

            state = llama.save_state()
            size = int(
                getattr(state, "llama_state_size", 0)
                or len(tokens) * FALLBACK_BYTES_PER_TOKEN
            )

            self._entries[key] = _Entry(tokens, state, size)
            self._evict(keep=key)

            logger.info(
                "Read {} instruction tokens once; cache holds {} prompt(s), "
                "{:.0f} MB.",
                len(tokens),
                len(self._entries),
                self.size / 1e6,
            )

            return True

        self.hits += 1
        self._entries.move_to_end(key)

        if not self._is_prefix(tokens, self._loaded_tokens(llama)):
            llama.load_state(entry.state)

        return True

    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(llama: Any, text: str) -> List[int]:
        return [
            int(token)
            for token in llama.tokenize(
                text.encode("utf-8"), add_bos=True, special=True
            )
        ]

    @staticmethod
    def _loaded_tokens(llama: Any) -> List[int]:
        ids = getattr(llama, "_input_ids", None)

        if ids is None:
            ids = getattr(llama, "input_ids", [])

        return [int(token) for token in ids[: int(getattr(llama, "n_tokens", 0))]]

    @staticmethod
    def _is_prefix(prefix: List[int], tokens: List[int]) -> bool:
        return bool(prefix) and tokens[: len(prefix)] == prefix

    def _evict(self, keep: str) -> None:
        while self.size > self.capacity and len(self._entries) > 1:
            oldest = next(iter(self._entries))

            if oldest == keep:
                self._entries.move_to_end(oldest)
                continue

            del self._entries[oldest]
