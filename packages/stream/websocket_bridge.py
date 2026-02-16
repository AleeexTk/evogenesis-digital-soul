"""WebSocket bridge broadcasting normalized task events."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from packages.coordination.shared_task_manager import SharedTaskManager

EVENTS = {
    "task.created",
    "agent.started",
    "agent.response",
    "task.completed",
    "task.failed",
}


def normalize_task_events(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in task.get("history", []):
        event = item.get("event")
        if event not in EVENTS:
            continue
        out.append(
            {
                "event": event,
                "task_id": task["id"],
                "status": task.get("status"),
                "agent": item.get("agent"),
                "timestamp": item.get("at"),
                "version": task.get("version"),
            }
        )
    return out


async def run_bridge(
    host: str = "0.0.0.0",
    port: int = 8765,
    state_path: str | Path = "shared_task.json",
    poll_interval_s: float = 0.5,
) -> None:
    try:
        import websockets
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install `websockets` to run the WS bridge") from exc

    manager = SharedTaskManager(state_path)
    clients: set[Any] = set()

    async def handler(websocket):
        clients.add(websocket)
        try:
            while True:
                await asyncio.sleep(15)
                await websocket.ping()
        finally:
            clients.discard(websocket)

    async def broadcaster():
        seen = set()
        while True:
            tasks = manager.list_tasks()
            frames = []
            for task in tasks:
                for event in normalize_task_events(task):
                    key = (event["task_id"], event["event"], event["version"], event["timestamp"])
                    if key in seen:
                        continue
                    seen.add(key)
                    frames.append(json.dumps(event, ensure_ascii=False))
            for frame in frames:
                for ws in list(clients):
                    try:
                        await ws.send(frame)
                    except Exception:
                        clients.discard(ws)
            await asyncio.sleep(poll_interval_s)

    async with websockets.serve(handler, host, port):
        await broadcaster()


if __name__ == "__main__":
    asyncio.run(run_bridge())
