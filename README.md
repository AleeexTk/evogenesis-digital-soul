# evogenesis-digital-soul

EvoGenesis / EvoPyramid agent runtime: single-agent PEAR loop, memory, governance, Termux edge, 3D pyramid UI.

## Coordination prototype (Sandbox migration)

This repository includes a JSON-backed multi-agent coordination loop inspired by the `Sandbox.txt` architecture:

- `packages/coordination/shared_task_manager.py` – shared state, atomic writes, file lock, optimistic task version checks, and transition validation.
- `packages/coordination/watcher_ark.py` – ARK watcher (`pending -> processing_by_ark -> processed_by_ark`).
- `packages/coordination/watcher_omega.py` – OMEGA watcher (`processed_by_ark -> processing_by_omega -> complete`).
- `packages/coordination/task_cli.py` – CLI manager (`create`, `show`, `reset`).
- `packages/stream/websocket_bridge.py` – websocket state streaming with heartbeat and stale-client cleanup.

Event contract entries emitted in task history:

- `task.created`
- `agent.started`
- `agent.response`
- `task.completed`
- `task.failed`

## Quick start

Create and inspect tasks:

```bash
python -m packages.coordination.task_cli create "Design an EvoGenesis memory policy"
python -m packages.coordination.task_cli show
```

Run watchers in separate shells:

```bash
python -m packages.coordination.watcher_ark
python -m packages.coordination.watcher_omega
```

Optional websocket stream (requires `websockets` package):

```bash
python -m packages.stream.websocket_bridge
```
