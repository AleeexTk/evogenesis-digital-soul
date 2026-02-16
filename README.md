# evogenesis-digital-soul

EvoGenesis / EvoPyramid agent runtime: single-agent PEAR loop, memory, governance, Termux edge, 3D pyramid UI.

## Coordination prototype (Sandbox migration)

This repository now includes a JSON-backed multi-agent coordination loop inspired by the `Sandbox.txt` architecture:

- `packages/coordination/shared_task_manager.py` – shared state, atomic writes, file lock, optimistic task version checks.
- `packages/coordination/watcher_ark.py` – ARK watcher (`pending -> processed_by_ark`).
- `packages/coordination/watcher_omega.py` – OMEGA watcher (`processed_by_ark -> complete`).
- `packages/stream/websocket_bridge.py` – websocket state streaming with heartbeat and stale-client cleanup.

## Quick start

```bash
python - <<'PY'
from packages.coordination.shared_task_manager import SharedTaskManager
m = SharedTaskManager()
print(m.create_task("Design an EvoGenesis memory policy"))
PY
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
