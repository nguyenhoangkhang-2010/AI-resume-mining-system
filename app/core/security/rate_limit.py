import threading
import time
from collections import deque
from typing import Callable, Deque, Dict, Optional

# Above this many tracked clients, idle ones are dropped.
CLEANUP_THRESHOLD = 10_000


class SlidingWindowLimiter:
    """
    Counts requests per client over a sliding window, in this process only
    (the API runs as a single worker; see docs/deployment.md).
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._hits: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def check(
        self,
        key: str,
        limit: int,
        window: float = 60.0,
    ) -> Optional[float]:
        """
        Records a request. Returns None when it is allowed, or the number of
        seconds to wait before retrying when the limit is exceeded (the
        rejected request is not recorded).
        """

        now = self._clock()

        with self._lock:
            hits = self._hits.setdefault(key, deque())

            while hits and now - hits[0] >= window:
                hits.popleft()

            if len(hits) >= limit:
                return max(0.0, window - (now - hits[0]))

            hits.append(now)

            if len(self._hits) > CLEANUP_THRESHOLD:
                self._drop_idle(now, window)

            return None

    def _drop_idle(self, now: float, window: float) -> None:
        idle = [
            key
            for key, hits in self._hits.items()
            if not hits or now - hits[-1] >= window
        ]

        for key in idle:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()
