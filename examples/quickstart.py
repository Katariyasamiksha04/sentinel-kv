"""
SentinelKV Quickstart Demo:
Demonstrates basic storage, TTL expiration, eviction, and WAL crash recovery.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sentinelkv import KeyValueStore, WALManager


def main():
    print("✨ Starting SentinelKV Quickstart Demo...\n")
    wal_file = "demo_kv.wal"
    wal = WALManager(wal_path=wal_file, sync_on_write=True)

    # 1. Initialize store with capacity 3 and WAL persistence
    store = KeyValueStore(max_capacity=3, wal_manager=wal)

    print("📥 Storing keys with LRU eviction threshold (max capacity = 3)...")
    store.set("session:user1", {"name": "Alice", "role": "engineer"})
    store.set("session:user2", {"name": "Bob", "role": "designer"})
    store.set("session:user3", {"name": "Charlie", "role": "manager"})

    # Access user1 to make it recently used
    store.get("session:user1")

    # Insert 4th item -> should evict user2 (the least recently used)
    print("➕ Inserting 4th item to trigger LRU eviction...")
    store.set("session:user4", {"name": "Diana", "role": "lead"})

    print("🔍 Querying items after eviction:")
    print(f"   user1 (recently used): {store.get('session:user1') is not None}")
    print(f"   user2 (evicted):       {store.get('session:user2') is not None}")
    print(f"   user3:                 {store.get('session:user3') is not None}")
    print(f"   user4:                 {store.get('session:user4') is not None}")

    # 2. TTL Expiration demo
    print("\n⏰ Testing TTL Expiration (0.3s)...")
    store.set("otp:auth", "849201", ttl_seconds=0.3)
    print(f"   Immediately: {store.get('otp:auth')}")
    time.sleep(0.4)
    print(f"   After 0.4s:  {store.get('otp:auth')} (Expired & purged)")

    store.close()

    # 3. Crash Recovery Simulation via WAL
    print("\n💥 Simulating unexpected crash and reconstructing state from WAL...")
    recovery_store = KeyValueStore(max_capacity=10)
    replayed = wal.replay(recovery_store)
    print(f"🔄 Replayed {replayed} operations from write-ahead log.")
    print(f"   Recovered session:user1: {recovery_store.get('session:user1')}")
    print(f"   Recovered session:user4: {recovery_store.get('session:user4')}")
    recovery_store.close()
    wal.close()

    if os.path.exists(wal_file):
        os.remove(wal_file)
    print("\n✅ Quickstart demo completed successfully!")


if __name__ == "__main__":
    main()
