import threading
import time
from collections import defaultdict, deque

from config import RATE_LIMIT_PER_MINUTE


class SlidingWindowLimiter:
    """Per-client sliding window, sized for isolate-local enforcement."""

    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        """Return (allowed, remaining). remaining is after this attempt."""
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.limit_per_minute:
                return False, 0
            bucket.append(now)
            remaining = self.limit_per_minute - len(bucket)
            return True, remaining

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def configure(self, limit_per_minute: int) -> None:
        with self._lock:
            self.limit_per_minute = limit_per_minute
            self._hits.clear()


limiter = SlidingWindowLimiter(limit_per_minute=RATE_LIMIT_PER_MINUTE)
