"""
Distributed Cluster Simulation using Consistent Hashing Ring.
Demonstrates key partitioning across nodes, virtual node distribution,
and minimal key rebalancing when adding/removing nodes.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sentinelkv.cluster.consistent_hash import ConsistentHashRing


def main():
    print("🌐 SentinelKV Distributed Cluster Partitioning Demo\n")

    ring = ConsistentHashRing(replicas=150)
    initial_nodes = ["cache-node-01", "cache-node-02", "cache-node-03"]
    for n in initial_nodes:
        ring.add_node(n)

    print(f"1️⃣ Ring initialized with {ring.total_nodes} nodes (150 virtual nodes each).")

    # Generate 3,000 keys
    keys = [f"user_session:{i:05d}" for i in range(3000)]
    initial_distribution = ring.get_distribution(keys)

    print("\n📊 Initial Key Distribution across 3 nodes:")
    for node, count in initial_distribution.items():
        pct = (count / len(keys)) * 100
        print(f"   {node}: {count:,} keys ({pct:.1f}%)")

    # Store baseline mapping
    baseline_map = {k: ring.get_node(k) for k in keys}

    # Scale cluster out: Add 4th node
    new_node = "cache-node-04"
    print(f"\n➕ Scaling out: Adding {new_node} to cluster...")
    ring.add_node(new_node)

    new_map = {k: ring.get_node(k) for k in keys}
    new_distribution = ring.get_distribution(keys)

    # Calculate key migration
    moved_keys = sum(1 for k in keys if baseline_map[k] != new_map[k])
    migration_pct = (moved_keys / len(keys)) * 100

    print("📊 Updated Key Distribution across 4 nodes:")
    for node, count in new_distribution.items():
        pct = (count / len(keys)) * 100
        print(f"   {node}: {count:,} keys ({pct:.1f}%)")

    print(f"\n⚡ Key Rebalancing Statistics:")
    print(f"   Total Keys Migrated: {moved_keys:,} ({migration_pct:.1f}%)")
    print(f"   Theoretical Ideal Migration (1/N = 1/4): 25.0%")
    print(f"   Keys preserved without cache-miss stampede: {len(keys) - moved_keys:,} ({(100 - migration_pct):.1f}%)")

    print("\n✅ Consistent Hashing cluster demo finished cleanly!")


if __name__ == "__main__":
    main()
