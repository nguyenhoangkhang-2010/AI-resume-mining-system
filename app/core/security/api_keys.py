import hashlib
import hmac
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Sequence, Tuple

ADMIN = "admin"
USER = "user"
ROLES = (ADMIN, USER)

# A short key is guessable; refuse it rather than accept it silently.
MIN_KEY_LENGTH = 24


@dataclass(frozen=True)
class Principal:
    """The caller behind a request. `name` is a key fingerprint, safe to log."""

    name: str
    role: str


ANONYMOUS = Principal(name="anonymous", role=ADMIN)


def fingerprint(key: str) -> str:
    return "key-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]


class ApiKeyStore:

    def __init__(self, entries: Sequence[Tuple[str, str]]):
        self._entries = [
            (role, key.encode("utf-8"), fingerprint(key)) for role, key in entries
        ]

    def __len__(self) -> int:
        return len(self._entries)

    def verify(self, candidate: str) -> Optional[Principal]:
        """
        Returns the caller for a key, or None. Every configured key is
        compared in constant time, with no early exit, so the response time
        does not reveal how much of a key was right.
        """

        encoded = candidate.encode("utf-8")
        match: Optional[Principal] = None

        for role, key, name in self._entries:
            if hmac.compare_digest(encoded, key):
                match = Principal(name=name, role=role)

        return match

    @classmethod
    def parse(cls, value: Optional[str]) -> "ApiKeyStore":
        """
        Parses "role:key,role:key". Raises ValueError for an unknown role,
        a key that is too short or a key listed twice.
        """

        entries = []
        seen = set()

        for item in (value or "").split(","):
            item = item.strip()

            if not item:
                continue

            role, separator, key = item.partition(":")

            role = role.strip().lower()
            key = key.strip()

            if not separator or role not in ROLES:
                raise ValueError(
                    f"API_KEYS entries must look like role:key with role "
                    f"one of {', '.join(ROLES)}."
                )

            if len(key) < MIN_KEY_LENGTH:
                raise ValueError(
                    f"An API key for role '{role}' is shorter than "
                    f"{MIN_KEY_LENGTH} characters."
                )

            if key in seen:
                raise ValueError("The same API key is listed twice.")

            seen.add(key)
            entries.append((role, key))

        return cls(entries)


@lru_cache(maxsize=4)
def key_store_for(value: Optional[str]) -> ApiKeyStore:
    return ApiKeyStore.parse(value)
