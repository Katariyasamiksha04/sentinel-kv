"""First-In-First-Out (FIFO) Eviction Policy."""

from __future__ import annotations
from collections import deque
from typing import Optional, Set
from sentinelkv.core.eviction.base import EvictionPolicy


class FIFOEvictionPolicy(EvictionPolicy):
    def __init__(self):
        self._queue = deque()
        self._set: Set[str] = set()

    def record_access(self, key: str) -> None:
        pass  # Access does not change insertion order in FIFO

    def record_insert(self, key: str) -> None:
        if key not in self._set:
            self._set.add(key)
            self._queue.append(key)

    def record_delete(self, key: str) -> None:
        self._set.discard(key)

    def evict_next(self) -> Optional[str]:
        while self._queue:
            candidate = self._queue.popleft()
            if candidate in self._set:
                self._set.remove(candidate)
                return candidate
        return None

    def size(self) -> int:
        return len(self._set)
