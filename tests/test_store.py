import time
import unittest
from sentinelkv.core.store import KeyValueStore


class TestKeyValueStore(unittest.TestCase):
    def setUp(self):
        self.store = KeyValueStore(max_capacity=5, num_shards=4)

    def tearDown(self):
        self.store.close()

    def test_basic_crud(self):
        self.store.set("user:1", {"name": "Alice"})
        self.assertEqual(self.store.get("user:1"), {"name": "Alice"})
        self.assertTrue(self.store.exists("user:1"))

        deleted = self.store.delete("user:1")
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get("user:1"))

    def test_ttl_expiration(self):
        # Set with 0.1s TTL
        self.store.set("temp_token", "secret123", ttl_seconds=0.1)
        self.assertEqual(self.store.get("temp_token"), "secret123")

        time.sleep(0.2)
        # Should be passively expired
        self.assertIsNone(self.store.get("temp_token"))

    def test_capacity_eviction(self):
        # Store has max_capacity = 5
        for i in range(5):
            self.store.set(f"k{i}", f"val{i}")

        self.assertEqual(self.store.size(), 5)

        # Adding 6th element triggers eviction
        self.store.set("k5", "val5")
        self.assertEqual(self.store.size(), 5)

        stats = self.store.stats()
        self.assertEqual(stats["evictions"], 1)


if __name__ == "__main__":
    unittest.main()
