"""
Telemetry, latency percentiles, and hit-ratio metrics collector.
"""

from __future__ import annotations
import threading
import time
from typing import Dict, List


class MetricsCollector:
    def __init__(self):
        self._latencies: List[float] = []
        self._lock = threading.Lock()

    def record_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._latencies.append(duration_ms)

    def get_summary(self) -> Dict[str, float]:
        with self._lock:
            if not self._latencies:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "count": 0}

            s = sorted(self._latencies)
            n = len(s)
            p50 = s[int(n * 0.50)]
            p95 = s[min(int(n * 0.95), n - 1)]
            p99 = s[min(int(n * 0.99), n - 1)]
            avg = sum(s) / n

            return {
                "count": n,
                "avg_ms": round(avg, 4),
                "p50_ms": round(p50, 4),
                "p95_ms": round(p95, 4),
                "p99_ms": round(p99, 4),
            }
