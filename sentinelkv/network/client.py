"""
SentinelKV TCP Client SDK.
"""

from __future__ import annotations
import json
import socket
from typing import Any, Dict, Optional


class SentinelClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None

    def connect(self) -> None:
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

    def _send_cmd(self, line: str) -> Dict[str, Any]:
        if not self._sock:
            self.connect()

        self._sock.sendall((line.strip() + "\n").encode("utf-8"))
        f = self._sock.makefile("r", encoding="utf-8")
        resp_line = f.readline()
        if not resp_line:
            raise ConnectionResetError("Server closed connection")
        return json.loads(resp_line)

    def get(self, key: str) -> Optional[Any]:
        res = self._send_cmd(f"GET {key}")
        return res.get("data")

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        cmd = f"SET {key} {value}"
        if ttl is not None:
            cmd += f" {ttl}"
        res = self._send_cmd(cmd)
        return res.get("status") == "OK"

    def delete(self, key: str) -> bool:
        res = self._send_cmd(f"DEL {key}")
        return bool(res.get("data"))

    def exists(self, key: str) -> bool:
        res = self._send_cmd(f"EXISTS {key}")
        return bool(res.get("data"))

    def ttl(self, key: str) -> Optional[float]:
        res = self._send_cmd(f"TTL {key}")
        return res.get("data")

    def stats(self) -> Dict[str, Any]:
        res = self._send_cmd("STATS")
        return res.get("data", {})

    def flush(self) -> None:
        self._send_cmd("FLUSH")

    def close(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None
