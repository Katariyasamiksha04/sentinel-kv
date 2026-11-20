"""
Asyncio-based TCP Server for SentinelKV.
Handles concurrent client socket connections with non-blocking I/O.
"""

from __future__ import annotations
import asyncio
import logging
import threading
from typing import Optional
from sentinelkv.core.store import KeyValueStore
from sentinelkv.network.protocol import ProtocolParser

logger = logging.getLogger("sentinelkv.server")


class SentinelServer:
    def __init__(self, store: KeyValueStore, host: str = "127.0.0.1", port: int = 6379):
        self.store = store
        self.host = host
        self.port = port
        self._server: Optional[asyncio.Server] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break

                cmd_text = line.decode("utf-8").strip()
                cmd = ProtocolParser.parse(cmd_text)
                if not cmd:
                    continue

                if cmd.verb == "GET":
                    if not cmd.args:
                        writer.write(ProtocolParser.format_error("Missing key argument for GET"))
                    else:
                        val = self.store.get(cmd.args[0])
                        writer.write(ProtocolParser.format_response("OK", val))

                elif cmd.verb == "SET":
                    if len(cmd.args) < 2:
                        writer.write(ProtocolParser.format_error("Usage: SET <key> <val> [ttl]"))
                    else:
                        key = cmd.args[0]
                        val = cmd.args[1]
                        ttl = float(cmd.args[2]) if len(cmd.args) >= 3 else None
                        self.store.set(key, val, ttl)
                        writer.write(ProtocolParser.format_response("OK", "STORED"))

                elif cmd.verb == "DEL":
                    if not cmd.args:
                        writer.write(ProtocolParser.format_error("Missing key argument for DEL"))
                    else:
                        deleted = self.store.delete(cmd.args[0])
                        writer.write(ProtocolParser.format_response("OK", deleted))

                elif cmd.verb == "EXISTS":
                    if not cmd.args:
                        writer.write(ProtocolParser.format_error("Missing key argument for EXISTS"))
                    else:
                        exists = self.store.exists(cmd.args[0])
                        writer.write(ProtocolParser.format_response("OK", exists))

                elif cmd.verb == "TTL":
                    if not cmd.args:
                        writer.write(ProtocolParser.format_error("Missing key argument for TTL"))
                    else:
                        remaining = self.store.ttl(cmd.args[0])
                        writer.write(ProtocolParser.format_response("OK", remaining))

                elif cmd.verb == "STATS":
                    writer.write(ProtocolParser.format_response("OK", self.store.stats()))

                elif cmd.verb == "FLUSH":
                    self.store.flush()
                    writer.write(ProtocolParser.format_response("OK", "CLEARED"))

                else:
                    writer.write(ProtocolParser.format_error(f"Unknown command '{cmd.verb}'"))

                await writer.drain()

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning(f"Client connection closed with error: {exc}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    def start(self) -> None:
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            async def _start():
                self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
                async with self._server:
                    await self._server.serve_forever()

            try:
                self._loop.run_until_complete(_start())
            except (asyncio.CancelledError, RuntimeError):
                pass

        self._thread = threading.Thread(target=run_loop, daemon=True, name="SentinelServer")
        self._thread.start()

    def stop(self) -> None:
        if self._loop and self._server:
            self._loop.call_soon_threadsafe(self._server.close)
            for task in asyncio.all_tasks(self._loop):
                self._loop.call_soon_threadsafe(task.cancel)
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
