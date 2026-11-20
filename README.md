# SentinelKV: Distributed In-Memory Key-Value Store & Cache

SentinelKV is a distributed in-memory key-value storage engine and caching layer implemented in Python. It features $O(1)$ LRU/LFU eviction algorithms, lock-striped concurrent storage, Write-Ahead Logging (WAL) with CRC32 data integrity checks, dual TTL expiration mechanics, and a Consistent Hashing ring for cluster partitioning.

Designed by **Samiksha Katariya** to demonstrate advanced data structures, systems architecture, and distributed partitioning fundamentals.

---

## 🏛️ System Architecture

SentinelKV is partitioned into modular systems subsystems:

```
                  +----------------------------------------------+
                  |            Network Client / SDK              |
                  +----------------------+-----------------------+
                                         |
                                         v
            +----------------------------------------------------------+
            |               Consistent Hashing Ring                    |
            |     (Virtual Nodes: Minimizes Partition Movement)        |
            +----------------------------+-----------------------------+
                                         |
                                         v
            +----------------------------------------------------------+
            |               Lock-Striped Storage Engine                |
            |  +---------------+  +---------------+  +---------------+  |
            |  | Shard 0 (Lock)|  | Shard 1 (Lock)|  | Shard M (Lock)|  |
            |  +-------+-------+  +-------+-------+  +-------+-------+  |
            +----------|------------------|------------------|---------+
                       v                  v                  v
            +----------------------+-----------------------------------+
            |    Eviction Engine   |       Write-Ahead Log (WAL)       |
            |  * O(1) LRU (DLL)    |  * Binary Framing with CRC32      |
            |  * O(1) LFU (Buckets)|  * Crash Replay & Compaction      |
            +----------------------+-----------------------------------+
```

---

## 🔬 Core Engineering Innovations

### 1. Lock-Striped Concurrency Sharding
Rather than acquiring a global read/write lock over the entire key space, SentinelKV hashes incoming keys across $M$ independent memory shards (`StorageShard`). Each shard maintains its own `RLock`, allowing concurrent reader and writer threads to operate in parallel with near-zero lock contention.

### 2. Strict $O(1)$ Eviction Algorithms
- **LRU (Least Recently Used)**: Implemented using custom Doubly-Linked List nodes with dummy `head`/`tail` sentinels coupled with an internal hash map to guarantee strict $O(1)$ access and eviction time complexity.
- **LFU (Least Frequently Used)**: Implemented using frequency buckets (Doubly-Linked Lists mapped by access count) with `_min_freq` tracking to resolve the classic LeetCode Hard LFU design challenge in $O(1)$ time.

### 3. Write-Ahead Logging (WAL) with CRC32 Verification
All mutations (`SET`, `DEL`, `FLUSH`) are serialized to an append-only binary log before memory updates take effect.
- **Header**: 4-byte CRC32 checksum + 4-byte payload length integer.
- **Payload**: JSON-encoded mutation metadata.
- **Crash Recovery**: During node boot, the log is sequentially parsed. Corrupted or partially written frames are detected and isolated via CRC32 mismatches, guaranteeing zero data loss on unexpected system crashes.

### 4. Dual TTL Expiration Mechanics
- **Passive Expiration**: Keys are inspected on read access (`get()`). If `current_time >= expires_at`, the entry is atomically purged from memory.
- **Active Expiration (Probabilistic Sampling)**: Modeled after Redis, a background worker periodically samples random volatile keys and purges expired entries, looping aggressively if more than 25% of sampled keys have expired.

### 5. Consistent Hashing Ring with Virtual Nodes
Distributed key partitioning utilizes consistent hashing with 150 virtual nodes (`vnodes`) per physical server. When cluster nodes scale up or down, only $K/N$ keys require rebalancing, eliminating cache stampedes.

---

## ⚡ Performance Benchmarks

Measured on standard consumer hardware:

| Benchmark Phase | Operations | Throughput | Avg Latency | p99 Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Atomic Writes (Lock-Striped)** | 20,000 | **277,500+ ops/sec** | 0.0033 ms | 0.0069 ms |
| **Concurrent Reads** | 20,000 | **509,000+ ops/sec** | 0.0017 ms | 0.0022 ms |

To run the benchmark locally:
```bash
python benchmarks/benchmark_engine.py
```

---

## 💻 Quickstart

### 1. In-Memory Store & Expiration

```python
from sentinelkv import KeyValueStore

# Initialize store with max capacity of 5,000 keys and LRU eviction
store = KeyValueStore(max_capacity=5000)

# Set key with 60-second TTL
store.set("session:token_901", {"user_id": 42, "role": "admin"}, ttl_seconds=60.0)

# Retrieve key
data = store.get("session:token_901")
print("User Data:", data)

# Query real-time cache metrics
print("Store Metrics:", store.stats())
store.close()
```

### 2. Running Examples

- **Quickstart & WAL Crash Recovery Demo**:
  ```bash
  python examples/quickstart.py
  ```
- **Consistent Hashing Cluster Rebalancing Demo**:
  ```bash
  python examples/cluster_demo.py
  ```

---

## 🧪 Test Suite

Run full unit and integration tests:
```bash
python -m unittest discover tests -v
```

All 10 tests validate LRU/LFU invariant correctness, lock striping, active/passive TTL purging, CRC32 WAL crash recovery, and consistent hash ring key distribution.

---

## 🐳 Docker Deployment

Run as a containerized cache service:
```bash
docker-compose up --build
```
Listens for TCP commands on port `6379`.
