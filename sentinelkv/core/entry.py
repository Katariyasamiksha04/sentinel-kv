"""Cache entry model with TTL expiration metadata and access tracking."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 1
    ttl_seconds: Optional[float] = None
    expires_at: Optional[float] = None
    version: int = 1

    def __post_init__(self):
        if self.ttl_seconds is not None and self.expires_at is None:
            self.expires_at = self.created_at + self.ttl_seconds

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    def touch(self) -> None:
        """Update access telemetry on cache hit."""
        self.last_accessed = time.time()
        self.access_count += 1

    def remaining_ttl(self) -> Optional[float]:
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0.0, remaining)
