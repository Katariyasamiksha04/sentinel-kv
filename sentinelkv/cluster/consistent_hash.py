"""
Consistent Hashing Ring with Virtual Nodes.
Prevents cache stampedes and hotspotting during distributed node scaling.
When a node is added or removed, only K/N keys are remapped.
"""

from __future__ import annotations
import bisect
import hashlib
from typing import Dict, List, Optional, Set


class ConsistentHashRing:
    def __init__(self, replicas: int = 150):
        self.replicas = max(10, replicas)
        self._ring: List[int] = []  # Sorted list of virtual node hashes
        self._hash_to_node: Dict[int, str] = {}
        self._nodes: Set[str] = set()

    def _hash(self, key: str) -> int:
        """MD5 128-bit hash integer."""
        return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """Add a physical node by generating virtual node positions along the 128-bit ring."""
        if node in self._nodes:
            return

        self._nodes.add(node)
        for i in range(self.replicas):
            vnode_key = f"{node}#vnode-{i}"
            h = self._hash(vnode_key)
            self._hash_to_node[h] = node
            bisect.insort(self._ring, h)

    def remove_node(self, node: str) -> None:
        """Remove physical node and strip its virtual points from the ring."""
        if node not in self._nodes:
            return

        self._nodes.remove(node)
        for i in range(self.replicas):
            vnode_key = f"{node}#vnode-{i}"
            h = self._hash(vnode_key)
            self._hash_to_node.pop(h, None)
            idx = bisect.bisect_left(self._ring, h)
            if idx < len(self._ring) and self._ring[idx] == h:
                self._ring.pop(idx)

    def get_node(self, key: str) -> Optional[str]:
        """Lookup destination node using clockwise binary search on the ring."""
        if not self._ring:
            return None

        h = self._hash(key)
        idx = bisect.bisect_right(self._ring, h)
        if idx == len(self._ring):
            idx = 0  # Wrap around the circular ring

        return self._hash_to_node[self._ring[idx]]

    def get_distribution(self, keys: List[str]) -> Dict[str, int]:
        """Compute key partition distribution metrics across all active nodes."""
        dist = {node: 0 for node in self._nodes}
        for k in keys:
            node = self.get_node(k)
            if node:
                dist[node] += 1
        return dist

    @property
    def total_nodes(self) -> int:
        return len(self._nodes)
