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

## Integration with EvoGenesis + EvoPyramid-ai (recommended contract)

### 1) Minimal network topology

- `evogenesis-digital-soul` (this repo): coordination + watchers + WS stream.
- `EvoGenesis`: receives normalized tasks on `POST /task`.
- `EvoPyramid-ai`: receives normalized UI/observability events on `POST /api/events` (and/or subscribes WS).

### 2) Shared env configuration

Use these environment variables in digital-soul:

```bash
export DIGITAL_SOUL_API_BASE="http://127.0.0.1:8080"
export EVOGENESIS_API_BASE="http://127.0.0.1:8090"
export EVOPYRAMID_API_BASE="http://127.0.0.1:5173"
export EVO_BRIDGE_AUTH_TOKEN="<optional-bearer-token>"
```

The config model is implemented in `packages/integration/bridge_config.py`.

### 3) Cross-repo relay client

`packages/integration/relay.py` provides:

- `relay_task_created(...)` -> sends task envelopes to `EvoGenesis /task`.
- `relay_task_update(...)` -> sends state events to `EvoPyramid-ai /api/events`.

This is stdlib-only (no `requests` dependency), so it is easy to run in constrained environments.

### 4) Recommended event payload (single contract)

```json
{
  "type": "task.state.updated",
  "payload": {
    "task_id": "<uuid>",
    "status": "processed_by_ark",
    "agent": "ark",
    "response": "..."
  }
}
```

Keep this envelope stable across all three repositories.

### 5) Quick local bring-up

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

If you need to forward events across repos, import and use `RelayClient` from `packages.integration.relay`.

## Russian quick answer to “как настроить связь?”

1. Зафиксируйте единый API-контракт (`/task`, `/api/events`, event envelope выше).
2. Поднимите три сервиса на разных портах и пропишите `EVOGENESIS_API_BASE` + `EVOPYRAMID_API_BASE`.
3. В `digital-soul` отправляйте `task.created` в EvoGenesis, а статусы/ответы агентов — в EvoPyramid-ai.
4. На фронте EvoPyramid-ai подписывайтесь на WS (`task.snapshot`, `task.state.updated`, `system.heartbeat`) для realtime.
5. Добавьте один общий Bearer token между сервисами (через `EVO_BRIDGE_AUTH_TOKEN`).
