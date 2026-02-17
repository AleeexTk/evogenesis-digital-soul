# evogenesis-digital-soul

EvoGenesis / EvoPyramid agent runtime: single-agent PEAR loop, memory, governance, Termux edge, 3D pyramid UI.

## Core role (Nexus / Core Host)

This repository is the **Core System Host** and contains:

- coordination/state-machine nucleus,
- integration/relay boundary to external services,
- execution adapters and workers.

## Architecture rules (fixed)

1. **One state machine**: source of truth is `SharedTaskManager`.
2. **Entry points in `/apps`** only.
3. **No imports from legacy** paths.

## Repository structure

```text
apps/
  nexus_daemon.py
  websocket_server.py
  execution_worker.py
packages/
  coordination/
  integration/
  execution/
    termux/
    session/
legacy/
  Project_Pyramid2024/
```

`legacy/Project_Pyramid2024` is archival only.

## Coordination prototype (Sandbox migration)

- `packages/coordination/shared_task_manager.py` – shared state, atomic writes, file lock, optimistic task version checks, transition validation.
- `packages/coordination/watcher_ark.py` – ARK watcher (`pending -> processing_by_ark -> processed_by_ark`).
- `packages/coordination/watcher_omega.py` – OMEGA watcher (`processed_by_ark -> processing_by_omega -> complete`).
- `packages/coordination/task_cli.py` – CLI manager (`create`, `show`, `reset`).
- `packages/stream/websocket_bridge.py` – websocket state streaming with heartbeat and stale-client cleanup.

Event contract in task history:

- `task.created`
- `agent.started`
- `agent.response`
- `task.completed`
- `task.failed`

Task identifiers are unified on each task object:

- `session_id`
- `task_id` (`id` field)
- `state_version`
- per-event `event_id`

## Execution adapter layer

- `packages/execution/termux/connector.py` – adapter boundary for termux execution.
- `packages/execution/worker.py` – execution worker pipeline:
  - `pending -> processing_by_exec -> done`
  - publishes updates back through `SharedTaskManager`
  - can relay events through `RelayClient`.

## Integration with EvoGenesis + EvoPyramid-ai

### Minimal network topology

- `evogenesis-digital-soul` (this repo): coordination + execution + WS stream.
- `EvoGenesis`: receives normalized tasks on `POST /task`.
- `EvoPyramid-ai`: receives normalized observability events on `POST /api/events`.

### Shared env configuration

```bash
export DIGITAL_SOUL_API_BASE="http://127.0.0.1:8080"
export EVOGENESIS_API_BASE="http://127.0.0.1:8090"
export EVOPYRAMID_API_BASE="http://127.0.0.1:5173"
export EVO_BRIDGE_AUTH_TOKEN="<optional-bearer-token>"
```

## Quick start

Create and inspect tasks:

```bash
python -m packages.coordination.task_cli create "Design an EvoGenesis memory policy"
python -m packages.coordination.task_cli show
```

Run services (separate shells):

```bash
python apps/nexus_daemon.py
python apps/execution_worker.py
python apps/websocket_server.py
```
