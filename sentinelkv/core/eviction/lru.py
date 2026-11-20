"""
O(1) Least Recently Used (LRU) Eviction Policy.
Implemented using a Doubly Linked List with dummy head/tail sentinels and a Hash Map.
"""

from __future__ import annotations
from typing import Dict, Optional
from sentinelkv.core.eviction.base import EvictionPolicy


class _Node:
    __slots__ = ("key", "prev", "next")

    def __init__(self, key: str = ""):
        self.key = key
        self.prev: Optional[_Node] = None
        self.next: Optional[_Node] = None


class LRUEvictionPolicy(EvictionPolicy):
    def __init__(self):
        self._map: Dict[str, _Node] = {}
        # Sentinels
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    def _remove_node(self, node: _Node) -> None:
        p = node.prev
        n = node.next
        if p:
            p.next = n
        if n:
            n.prev = p
        node.prev = None
        node.next = None

    def _add_to_tail(self, node: _Node) -> None:
        last = self._tail.prev
        last.next = node
        node.prev = last
        node.next = self._tail
        self._tail.prev = node

    def record_access(self, key: str) -> None:
        node = self._map.get(key)
        if node:
            self._remove_node(node)
            self._add_to_tail(node)

    def record_insert(self, key: str) -> None:
        if key in self._map:
            self.record_access(key)
            return

        new_node = _Node(key)
        self._map[key] = new_node
        self._add_to_tail(new_node)

    def record_delete(self, key: str) -> None:
        node = self._map.pop(key, None)
        if node:
            self._remove_node(node)

    def evict_next(self) -> Optional[str]:
        if not self._map:
            return None

        # The least recently used node is right after head
        lru_node = self._head.next
        if lru_node == self._tail:
            return None

        evicted_key = lru_node.key
        self._remove_node(lru_node)
        self._map.pop(evicted_key, None)
        return evicted_key

    def size(self) -> int:
        return len(self._map)
