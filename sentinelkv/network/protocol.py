"""
Wire protocol parser and serializer for SentinelKV.
Supports text-based line protocol:
- SET <key> <value> [TTL_SECONDS]
- GET <key>
- DEL <key>
- EXISTS <key>
- TTL <key>
- STATS
- FLUSH
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Command:
    verb: str
    args: List[str]


class ProtocolParser:
    @staticmethod
    def parse(line: str) -> Optional[Command]:
        parts = line.strip().split()
        if not parts:
            return None
        return Command(verb=parts[0].upper(), args=parts[1:])

    @staticmethod
    def format_response(status: str, data: Any = None) -> bytes:
        response = {"status": status}
        if data is not None:
            response["data"] = data
        return (json.dumps(response) + "\n").encode("utf-8")

    @staticmethod
    def format_error(message: str) -> bytes:
        return (json.dumps({"status": "ERR", "message": message}) + "\n").encode("utf-8")
