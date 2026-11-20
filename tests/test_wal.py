import os
import tempfile
import unittest
from sentinelkv.core.store import KeyValueStore
from sentinelkv.wal.wal_manager import WALManager


class TestWALManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.wal_path = os.path.join(self.temp_dir.name, "test.wal")
        self.wal = WALManager(wal_path=self.wal_path, sync_on_write=True)

    def tearDown(self):
        self.wal.close()
        self.temp_dir.cleanup()

    def test_wal_crash_recovery(self):
        # 1. Initialize store with WAL
        store1 = KeyValueStore(wal_manager=self.wal)
        store1.set("session:abc", "user_42")
        store1.set("config:theme", "dark")
        store1.delete("config:theme")
        store1.set("session:def", "user_99")
        store1.close()

        # 2. Replay log into fresh store instance
        store2 = KeyValueStore()
        replayed = self.wal.replay(store2)

        self.assertEqual(replayed, 4)
        self.assertEqual(store2.get("session:abc"), "user_42")
        self.assertEqual(store2.get("session:def"), "user_99")
        self.assertIsNone(store2.get("config:theme"))
        store2.close()


if __name__ == "__main__":
    unittest.main()
