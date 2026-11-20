"""Core storage primitives, cache entry models, and eviction interfaces."""

from sentinelkv.core.entry import CacheEntry
from sentinelkv.core.store import KeyValueStore

__all__ = ["CacheEntry", "KeyValueStore"]
