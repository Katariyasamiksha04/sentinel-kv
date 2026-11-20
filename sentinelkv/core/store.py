"""
Concurrent Key-Value Storage Engine.
Uses lock-striping / sharding to minimize thread contention, integrates O(1) eviction
policies, and provides atomic write-ahead logging (WAL) hooks.
"""

from __future__ import annotations
import hashlib
import threading
import time
from typing import Any, Dict, List, Optional
from sentinelkv.core.entry import CacheEntry
from sentinelkv.core.eviction.base import EvictionPolicy
from sentinelkv.core.eviction.lru import LRUEvictionPolicy
from sentinelkv.core.expiration import ExpirationManager


class StorageShard:
    """Independent lock-striped memory shard."""

    def __init__(self, eviction_policy: EvictionPolicy):
        self.data: Dict[str, CacheEntry] = {}
        self.eviction = eviction_policy
        self.lock = threading.RLock()


class KeyValueStore:
    def __init__(
        self,
        max_capacity: int = 10000,
        num_shards: int = 16,
        eviction_factory=None,
        wal_manager=None,
    ):
        self.max_capacity = max_capacity
        self.num_shards = max(1, num_shards)
        self.wal_manager = wal_manager

        if eviction_factory is None:
            eviction_factory = LRUEvictionPolicy

        self._shards: List[StorageShard] = [
            StorageShard(eviction_policy=eviction_factory()) for _ in range(self.num_shards)
        ]

        # Global stats lock
        self._stats_lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expired = 0

        # Background active TTL expiration
        self.expiration_mgr = ExpirationManager(
            expiry_checker=self._is_key_expired,
            deleter=self.delete,
            interval_seconds=0.2,
        )
        self.expiration_mgr.start()

    def _get_shard(self, key: str) -> StorageShard:
        idx = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % self.num_shards
        return self._shards[idx]

    def _is_key_expired(self, key: str) -> bool:
        shard = self._get_shard(key)
        with shard.lock:
            entry = shard.data.get(key)
            return entry.is_expired if entry else False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve key value with passive TTL expiration check and O(1) access recording."""
        shard = self._get_shard(key)
        with shard.lock:
            entry = shard.data.get(key)

            if entry is None:
                with self._stats_lock:
                    self._misses += 1
                return None

            # Passive expiration check
            if entry.is_expired:
                shard.data.pop(key, None)
                shard.eviction.record_delete(key)
                self.expiration_mgr.unregister_ttl(key)
                with self._stats_lock:
                    self._misses += 1
                    self._expired += 1
                return None

            entry.touch()
            shard.eviction.record_access(key)
            with self._stats_lock:
                self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> bool:
        """Store key-value pair with optional TTL and automatic capacity eviction."""
        # 1. Write to WAL first for ACID durability
        if self.wal_manager:
            self.wal_manager.log_set(key, value, ttl_seconds)

        shard = self._get_shard(key)
        with shard.lock:
            # Capacity check: total items across shards
            current_total = self.size()
            if key not in shard.data and current_total >= self.max_capacity:
                self._evict_one()

            now = time.time()
            exp = now + ttl_seconds if ttl_seconds is not None else None
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                ttl_seconds=ttl_seconds,
                expires_at=exp,
            )

            is_new = key not in shard.data
            shard.data[key] = entry

            if is_new:
                shard.eviction.record_insert(key)
            else:
                shard.eviction.record_access(key)

            if exp is not None:
                self.expiration_mgr.register_ttl(key, exp)
            else:
                self.expiration_mgr.unregister_ttl(key)

            return True

    def _evict_one(self) -> None:
        """Evict one entry using the eviction policy of the most loaded shard."""
        target_shard = max(self._shards, key=lambda s: len(s.data))
        with target_shard.lock:
            evicted_key = target_shard.eviction.evict_next()
            if evicted_key:
                target_shard.data.pop(evicted_key, None)
                self.expiration_mgr.unregister_ttl(evicted_key)
                with self._stats_lock:
                    self._evictions += 1

    def delete(self, key: str) -> bool:
        """Remove key from store."""
        if self.wal_manager:
            self.wal_manager.log_delete(key)

        shard = self._get_shard(key)
        with shard.lock:
            if key in shard.data:
                del shard.data[key]
                shard.eviction.record_delete(key)
                self.expiration_mgr.unregister_ttl(key)
                return True
            return False

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def ttl(self, key: str) -> Optional[float]:
        shard = self._get_shard(key)
        with shard.lock:
            entry = shard.data.get(key)
            if not entry or entry.is_expired:
                return None
            return entry.remaining_ttl()

    def size(self) -> int:
        return sum(len(s.data) for s in self._shards)

    def flush(self) -> None:
        """Purge all stored keys."""
        if self.wal_manager:
            self.wal_manager.log_flush()

        for shard in self._shards:
            with shard.lock:
                shard.data.clear()
        with self._stats_lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expired = 0

    def stats(self) -> Dict[str, Any]:
        with self._stats_lock:
            total_ops = self._hits + self._misses
            hit_ratio = (self._hits / total_ops) if total_ops > 0 else 0.0
            return {
                "size": self.size(),
                "max_capacity": self.max_capacity,
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(hit_ratio, 4),
                "evictions": self._evictions,
                "expired": self._expired,
            }

    def close(self) -> None:
        self.expiration_mgr.stop()
        if self.wal_manager:
            self.wal_manager.close()
