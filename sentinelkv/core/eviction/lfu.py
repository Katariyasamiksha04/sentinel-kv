"""
O(1) Least Frequently Used (LFU) Eviction Policy.
Maintains frequency doubly-linked lists and tracks min_frequency for strict O(1) operations.
"""

from __future__ import annotations
from typing import Dict, Optional
from sentinelkv.core.eviction.base import EvictionPolicy


class _LFUNode:
    __slots__ = ("key", "freq", "prev", "next")

    def __init__(self, key: str = "", freq: int = 1):
        self.key = key
        self.freq = freq
        self.prev: Optional[_LFUNode] = None
        self.next: Optional[_LFUNode] = None


class _DoublyLinkedList:
    def __init__(self):
        self.head = _LFUNode()
        self.tail = _LFUNode()
        self.head.next = self.tail
        self.tail.prev = self.head
        self._count = 0

    def add_to_tail(self, node: _LFUNode) -> None:
        last = self.tail.prev
        last.next = node
        node.prev = last
        node.next = self.tail
        self.tail.prev = node
        self._count += 1

    def remove(self, node: _LFUNode) -> None:
        p = node.prev
        n = node.next
        if p:
            p.next = n
        if n:
            n.prev = p
        node.prev = None
        node.next = None
        self._count -= 1

    def pop_head(self) -> Optional[_LFUNode]:
        if self._count == 0:
            return None
        first = self.head.next
        self.remove(first)
        return first

    def is_empty(self) -> bool:
        return self._count == 0


class LFUEvictionPolicy(EvictionPolicy):
    def __init__(self):
        self._node_map: Dict[str, _LFUNode] = {}
        self._freq_map: Dict[int, _DoublyLinkedList] = {}
        self._min_freq: int = 0

    def _get_freq_list(self, freq: int) -> _DoublyLinkedList:
        if freq not in self._freq_map:
            self._freq_map[freq] = _DoublyLinkedList()
        return self._freq_map[freq]

    def record_access(self, key: str) -> None:
        node = self._node_map.get(key)
        if not node:
            return

        old_freq = node.freq
        old_list = self._freq_map[old_freq]
        old_list.remove(node)

        if old_list.is_empty():
            del self._freq_map[old_freq]
            if self._min_freq == old_freq:
                self._min_freq += 1

        node.freq += 1
        new_list = self._get_freq_list(node.freq)
        new_list.add_to_tail(node)

    def record_insert(self, key: str) -> None:
        if key in self._node_map:
            self.record_access(key)
            return

        node = _LFUNode(key=key, freq=1)
        self._node_map[key] = node
        freq_list = self._get_freq_list(1)
        freq_list.add_to_tail(node)
        self._min_freq = 1

    def record_delete(self, key: str) -> None:
        node = self._node_map.pop(key, None)
        if not node:
            return

        freq_list = self._freq_map.get(node.freq)
        if freq_list:
            freq_list.remove(node)
            if freq_list.is_empty():
                del self._freq_map[node.freq]
                if self._min_freq == node.freq:
                    self._min_freq = min(self._freq_map.keys(), default=0)

    def evict_next(self) -> Optional[str]:
        if not self._node_map:
            return None

        freq_list = self._freq_map.get(self._min_freq)
        if not freq_list:
            return None

        node = freq_list.pop_head()
        if not node:
            return None

        self._node_map.pop(node.key, None)
        if freq_list.is_empty():
            del self._freq_map[self._min_freq]
            if self._freq_map:
                self._min_freq = min(self._freq_map.keys())
            else:
                self._min_freq = 0

        return node.key

    def size(self) -> int:
        return len(self._node_map)
