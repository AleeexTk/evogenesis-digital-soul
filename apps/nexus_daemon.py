"""Run ARK and OMEGA watchers together."""

from __future__ import annotations

import threading

from packages.coordination.shared_task_manager import SharedTaskManager
from packages.coordination.watcher_ark import ArkWatcher
from packages.coordination.watcher_omega import OmegaWatcher


if __name__ == "__main__":
    manager = SharedTaskManager()
    ark = ArkWatcher(manager)
    omega = OmegaWatcher(manager)

    t1 = threading.Thread(target=ark.run_forever, daemon=True)
    t2 = threading.Thread(target=omega.run_forever, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
