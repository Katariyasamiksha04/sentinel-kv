"""
SentinelKV: High-Performance Distributed In-Memory Key-Value Store & Cache.
Engineered with O(1) eviction algorithms, write-ahead logging (WAL), TTL expiration,
and consistent hashing partition balancing.
"""

__version__ = "1.0.0"
__author__ = "Samiksha Katariya"

from sentinelkv.core.store import KeyValueStore
from sentinelkv.core.eviction.lru import LRUEvictionPolicy
from sentinelkv.core.eviction.lfu import LFUEvictionPolicy
from sentinelkv.wal.wal_manager import WALManager
from sentinelkv.cluster.consistent_hash import ConsistentHashRing
from sentinelkv.network.client import SentinelClient

__all__ = [
    "KeyValueStore",
    "LRUEvictionPolicy",
    "LFUEvictionPolicy",
    "WALManager",
    "ConsistentHashRing",
    "SentinelClient",
]
