"""WebSocket bridge to stream shared task state updates to clients."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Set

from packages.coordination.shared_task_manager import SharedTaskManager

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:  # pragma: no cover
    websockets = None
    WebSocketServerProtocol = Any


def normalize_task_events(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize one task's history into event frames with event-local status/version."""
    history = task.get("history", [])
    if not history:
        return []

    normalized: List[Dict[str, Any]] = []
    running_status = "pending"
    running_version: int | None = None

    for index, entry in enumerate(history):
        event_type = entry.get("event", "task.updated")

        inferred_status = entry.get("status")
        if inferred_status is None:
            if event_type == "task.created":
                inferred_status = "pending"
            elif event_type == "task.completed":
                inferred_status = "complete"
            elif event_type == "task.failed":
                inferred_status = "failed"
            else:
                inferred_status = running_status

        inferred_version = entry.get("version")
        if inferred_version is None:
            if event_type == "task.created" and index == 0:
                inferred_version = 0
            elif running_version is None:
                inferred_version = 0
            else:
                inferred_version = running_version + 1

        running_status = inferred_status
        running_version = inferred_version

        normalized.append(
            {
                "type": event_type,
                "payload": {
                    "task_id": task.get("id"),
                    "status": running_status,
                    "version": inferred_version,
                    "at": entry.get("at"),
                    "agent": entry.get("agent"),
                    "response": entry.get("response"),
                    "metadata": entry.get("metadata"),
                },
            }
        )

    return normalized


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
        self._last_history_lengths: Dict[str, int] = {}

    async def _register(self, ws: WebSocketServerProtocol) -> None:
        self.clients.add(ws)
        await ws.send(json.dumps({"type": "task.snapshot", "payload": self.manager.read_state()}))

    async def _unregister(self, ws: WebSocketServerProtocol) -> None:
        self.clients.discard(ws)

    async def _broadcast(self, event: Dict[str, Any]) -> None:
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
                state = self.manager.read_state()
                await self._broadcast(
                    {
                        "type": "task.state.updated",
                        "payload": state,
                    }
                )
                for task in state.get("tasks", []):
                    task_id = task.get("id")
                    if not task_id:
                        continue
                    frames = normalize_task_events(task)
                    start = self._last_history_lengths.get(task_id, 0)
                    for frame in frames[start:]:
                        await self._broadcast(frame)
                    self._last_history_lengths[task_id] = len(frames)
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
        if websockets is None:  # pragma: no cover
            raise RuntimeError("Install websockets to run websocket_bridge.py")
        async with websockets.serve(self._handler, self.host, self.port):
            await asyncio.gather(self._watch_file(), self._heartbeat())


if __name__ == "__main__":
    asyncio.run(WebSocketBridge(SharedTaskManager()).serve())
