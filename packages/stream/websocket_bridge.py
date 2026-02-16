"""WebSocket bridge to stream shared task state updates to clients."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Set

from packages.coordination.shared_task_manager import SharedTaskManager

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Install websockets to run websocket_bridge.py") from exc


class WebSocketBridge:
    def __init__(
        self,
        manager: SharedTaskManager,
        state_file: str | Path = "shared_task.json",
        host: str = "0.0.0.0",
        port: int = 8765,
        heartbeat_s: int = 15,
    ) -> None:
        self.manager = manager
        self.state_file = Path(state_file)
        self.host = host
        self.port = port
        self.heartbeat_s = heartbeat_s
        self.clients: Set[WebSocketServerProtocol] = set()

    async def _register(self, ws: WebSocketServerProtocol) -> None:
        self.clients.add(ws)
        await ws.send(json.dumps({"type": "task.snapshot", "payload": self.manager.read_state()}))

    async def _unregister(self, ws: WebSocketServerProtocol) -> None:
        self.clients.discard(ws)

    async def _broadcast(self, event: dict) -> None:
        if not self.clients:
            return
        payload = json.dumps(event)
        stale = set()
        for client in list(self.clients):
            try:
                await client.send(payload)
            except Exception:
                stale.add(client)
        for client in stale:
            await self._unregister(client)

    async def _watch_file(self) -> None:
        last_mtime = 0.0
        while True:
            try:
                mtime = self.state_file.stat().st_mtime
            except FileNotFoundError:
                mtime = 0.0
            if mtime > last_mtime:
                last_mtime = mtime
                await self._broadcast(
                    {
                        "type": "task.state.updated",
                        "payload": self.manager.read_state(),
                    }
                )
            await asyncio.sleep(0.5)

    async def _heartbeat(self) -> None:
        while True:
            await self._broadcast({"type": "system.heartbeat"})
            await asyncio.sleep(self.heartbeat_s)

    async def _handler(self, ws: WebSocketServerProtocol) -> None:
        await self._register(ws)
        try:
            async for _ in ws:
                pass
        finally:
            await self._unregister(ws)

    async def serve(self) -> None:
        async with websockets.serve(self._handler, self.host, self.port):
            await asyncio.gather(self._watch_file(), self._heartbeat())


if __name__ == "__main__":
    asyncio.run(WebSocketBridge(SharedTaskManager()).serve())
