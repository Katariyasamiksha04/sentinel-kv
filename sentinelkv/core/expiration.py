"""
TTL Expiration Manager.
Implements dual expiration mechanisms:
1. Passive expiration: On-access detection during get/ttl calls.
2. Active expiration: Background probabilistic sampling loop modeled after Redis.
"""

from __future__ import annotations
import logging
import random
import threading
import time
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("sentinelkv.expiration")


class ExpirationManager:
    def __init__(
        self,
        expiry_checker: Callable[[str], bool],
        deleter: Callable[[str], None],
        sample_size: int = 20,
        interval_seconds: float = 0.5,
    ):
        self.expiry_checker = expiry_checker
        self.deleter = deleter
        self.sample_size = sample_size
        self.interval_seconds = interval_seconds

        self._ttl_keys: Dict[str, float] = {}  # key -> expires_at
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def register_ttl(self, key: str, expires_at: float) -> None:
        with self._lock:
            self._ttl_keys[key] = expires_at

    def unregister_ttl(self, key: str) -> None:
        with self._lock:
            self._ttl_keys.pop(key, None)

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._active_expiration_loop, daemon=True, name="TTLExpiration")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _active_expiration_loop(self) -> None:
        """
        Sample up to sample_size random volatile keys.
        Delete keys that expired. If >25% of sampled keys were expired, repeat immediately.
        """
        while not self._stop_event.is_set():
            with self._lock:
                keys = list(self._ttl_keys.keys())

            if not keys:
                time.sleep(self.interval_seconds)
                continue

            sample = random.sample(keys, min(len(keys), self.sample_size))
            now = time.time()
            expired_count = 0

            for k in sample:
                with self._lock:
                    exp = self._ttl_keys.get(k)
                if exp and exp <= now:
                    self.deleter(k)
                    self.unregister_ttl(k)
                    expired_count += 1

            if len(sample) > 0 and (expired_count / len(sample)) > 0.25:
                # High expiration density: loop again immediately without sleep
                continue

            time.sleep(self.interval_seconds)
