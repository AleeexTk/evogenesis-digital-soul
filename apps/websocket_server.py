"""Run websocket bridge service."""

import asyncio

from packages.coordination.shared_task_manager import SharedTaskManager
from packages.stream.websocket_bridge import WebSocketBridge


if __name__ == "__main__":
    asyncio.run(WebSocketBridge(SharedTaskManager()).serve())
