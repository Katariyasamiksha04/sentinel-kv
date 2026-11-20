"""
Performance benchmark for SentinelKV.
Measures read/write throughput and latency percentiles under lock-striping.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sentinelkv.core.store import KeyValueStore
from sentinelkv.metrics import MetricsCollector


def run_benchmark(num_ops: int = 20000):
    print("=" * 60)
    print(f"🚀 SentinelKV Engine Benchmark ({num_ops:,} Operations)")
    print("=" * 60)

    store = KeyValueStore(max_capacity=50000, num_shards=16)
    metrics = MetricsCollector()

    # 1. Write Benchmark
    start_writes = time.perf_counter()
    for i in range(num_ops):
        t0 = time.perf_counter()
        store.set(f"user:session:{i}", {"uid": i, "role": "admin"})
        metrics.record_latency((time.perf_counter() - t0) * 1000)
    write_duration = time.perf_counter() - start_writes
    write_ops = num_ops / write_duration
    write_summary = metrics.get_summary()

    print(f"✅ Writes:  {write_duration:.3f}s | {write_ops:,.0f} ops/sec | Avg: {write_summary['avg_ms']}ms | p99: {write_summary['p99_ms']}ms")

    # 2. Read Benchmark
    read_metrics = MetricsCollector()
    start_reads = time.perf_counter()
    for i in range(num_ops):
        t0 = time.perf_counter()
        store.get(f"user:session:{i}")
        read_metrics.record_latency((time.perf_counter() - t0) * 1000)
    read_duration = time.perf_counter() - start_reads
    read_ops = num_ops / read_duration
    read_summary = read_metrics.get_summary()

    print(f"✅ Reads:   {read_duration:.3f}s | {read_ops:,.0f} ops/sec | Avg: {read_summary['avg_ms']}ms | p99: {read_summary['p99_ms']}ms")

    stats = store.stats()
    print(f"📊 Hit Ratio: {stats['hit_ratio'] * 100:.1f}% | Total Items: {stats['size']:,}")
    print("=" * 60)
    store.close()


if __name__ == "__main__":
    run_benchmark(num_ops=20000)
