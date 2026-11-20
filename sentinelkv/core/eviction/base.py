"""Abstract interface for cache eviction algorithms."""

from __future__ import annotations
import abc
from typing import Optional


class EvictionPolicy(abc.ABC):
    @abc.abstractmethod
    def record_access(self, key: str) -> None:
        """Invoked whenever a key is retrieved or updated."""
        pass

    @abc.abstractmethod
    def record_insert(self, key: str) -> None:
        """Invoked when a new key is added to the store."""
        pass

    @abc.abstractmethod
    def record_delete(self, key: str) -> None:
        """Invoked when a key is removed explicitly."""
        pass

    @abc.abstractmethod
    def evict_next(self) -> Optional[str]:
        """Select and remove the optimal candidate key for eviction."""
        pass

    @abc.abstractmethod
    def size(self) -> int:
        pass
