import threading
import time
from collections import OrderedDict

from config import L1_CACHE_MAXSIZE, L1_CACHE_TTL_SECONDS


class L1Cache:
    """In-isolate LRU with TTL. Lookups are dict + lock, typically well under 0.1ms."""

    def __init__(self, maxsize: int = 4096, ttl_seconds: float = 30.0) -> None:
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._data: OrderedDict[str, tuple[float, object]] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if expires_at < now:
                del self._data[key]
                self.misses += 1
                return None
            self._data.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: str, value: object) -> None:
        expires_at = time.monotonic() + self.ttl_seconds
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (expires_at, value)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [key for key in self._data if key.startswith(prefix)]
            for key in keys:
                del self._data[key]
            return len(keys)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict:
        with self._lock:
            total = self.hits + self.misses
            hit_ratio = (self.hits / total) if total else 0.0
            return {
                "size": len(self._data),
                "maxsize": self.maxsize,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": round(hit_ratio, 4),
            }


l1 = L1Cache(maxsize=L1_CACHE_MAXSIZE, ttl_seconds=L1_CACHE_TTL_SECONDS)
