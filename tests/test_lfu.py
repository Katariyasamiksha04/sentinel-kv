import unittest
from sentinelkv.core.eviction.lfu import LFUEvictionPolicy


class TestLFUEvictionPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = LFUEvictionPolicy()

    def test_lfu_frequency_eviction(self):
        self.policy.record_insert("k1")  # freq 1
        self.policy.record_insert("k2")  # freq 1
        self.policy.record_insert("k3")  # freq 1

        # Access k1 twice -> freq 3
        self.policy.record_access("k1")
        self.policy.record_access("k1")

        # Access k2 once -> freq 2
        self.policy.record_access("k2")

        # k3 has freq 1, so it should be evicted first
        self.assertEqual(self.policy.evict_next(), "k3")

        # Next lowest is k2 (freq 2)
        self.assertEqual(self.policy.evict_next(), "k2")

        # Finally k1 (freq 3)
        self.assertEqual(self.policy.evict_next(), "k1")


if __name__ == "__main__":
    unittest.main()
