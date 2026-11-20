import unittest
from sentinelkv.cluster.consistent_hash import ConsistentHashRing


class TestConsistentHashRing(unittest.TestCase):
    def setUp(self):
        self.ring = ConsistentHashRing(replicas=100)

    def test_node_addition_and_lookup(self):
        self.ring.add_node("node-1")
        self.ring.add_node("node-2")
        self.ring.add_node("node-3")

        node = self.ring.get_node("user_1001")
        self.assertIn(node, {"node-1", "node-2", "node-3"})

        # Key lookup should be deterministic
        self.assertEqual(self.ring.get_node("user_1001"), node)

    def test_partition_distribution(self):
        nodes = ["cache-a", "cache-b", "cache-c"]
        for n in nodes:
            self.ring.add_node(n)

        keys = [f"key_{i}" for i in range(1000)]
        distribution = self.ring.get_distribution(keys)

        # Each node should receive a fair share of the 1000 keys (e.g. at least 200)
        for n in nodes:
            self.assertGreater(distribution[n], 200)

    def test_node_removal_minimizes_movement(self):
        self.ring.add_node("node-1")
        self.ring.add_node("node-2")
        self.ring.add_node("node-3")

        keys = [f"item_{i}" for i in range(200)]
        initial_mapping = {k: self.ring.get_node(k) for k in keys}

        # Remove node-3
        self.ring.remove_node("node-3")

        # Keys mapped to node-1 and node-2 should NOT move!
        remapped_unnecessarily = 0
        for k in keys:
            if initial_mapping[k] in ("node-1", "node-2"):
                if self.ring.get_node(k) != initial_mapping[k]:
                    remapped_unnecessarily += 1

        self.assertEqual(remapped_unnecessarily, 0)


if __name__ == "__main__":
    unittest.main()
