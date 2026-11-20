import unittest
from sentinelkv.core.eviction.lru import LRUEvictionPolicy


class TestLRUEvictionPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = LRUEvictionPolicy()

    def test_lru_order(self):
        self.policy.record_insert("k1")
        self.policy.record_insert("k2")
        self.policy.record_insert("k3")

        # k1 is oldest, should evict first
        self.assertEqual(self.policy.evict_next(), "k1")

        # Access k2 to make it most recently used
        self.policy.record_access("k2")

        # Now k3 is oldest
        self.assertEqual(self.policy.evict_next(), "k3")
        self.assertEqual(self.policy.evict_next(), "k2")
        self.assertIsNone(self.policy.evict_next())

    def test_delete_removes_from_policy(self):
        self.policy.record_insert("k1")
        self.policy.record_insert("k2")
        self.policy.record_delete("k1")

        self.assertEqual(self.policy.evict_next(), "k2")
        self.assertIsNone(self.policy.evict_next())


if __name__ == "__main__":
    unittest.main()
