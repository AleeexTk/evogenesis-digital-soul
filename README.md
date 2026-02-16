# evogenesis-digital-soul

EvoGenesis / EvoPyramid agent runtime: single-agent PEAR loop, memory, governance, Termux edge, 3D pyramid UI.

## Coordination prototype (sandbox migration)

This repo now includes a local, JSON-backed coordination layer with:

- `packages/coordination/shared_task_manager.py` - atomic JSON state + lock file + optimistic concurrency (`version`).
- `packages/coordination/watcher_ark.py` - polling agent watcher for Ark.
- `packages/coordination/watcher_omega.py` - polling agent watcher for Omega.
- `packages/coordination/task_cli.py` - CLI for create/show/reset.
- `packages/stream/websocket_bridge.py` - WebSocket bridge with normalized event contract.

## Event contract

Bridge emits the following normalized events for UI consumption:

- `task.created`
- `agent.started`
- `agent.response`
- `task.completed`
- `task.failed`

Each event includes `task_id`, `status`, `agent`, `timestamp`, and `version`.

## Quickstart

Create a task:

```bash
python -m packages.coordination.task_cli create "Analyze EvoGenesis archive"
```

Show current tasks:

```bash
python -m packages.coordination.task_cli show
```

Run watcher(s) in separate terminals:

```bash
python -m packages.coordination.watcher_ark
python -m packages.coordination.watcher_omega
```

Run WebSocket bridge (requires `websockets`):

```bash
python -m packages.stream.websocket_bridge
```
