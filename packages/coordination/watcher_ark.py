"""ARK watcher: claims pending tasks and records ARK responses."""

from __future__ import annotations

import time
from typing import Callable

from .shared_task_manager import SharedTaskManager, TaskConflictError, TaskUpdate


class ArkWatcher:
    def __init__(
        self,
        manager: SharedTaskManager,
        process_fn: Callable[[str], str] | None = None,
        poll_interval: float = 0.75,
    ) -> None:
        self.manager = manager
        self.poll_interval = poll_interval
        self.process_fn = process_fn or (lambda prompt: f"ARK processed: {prompt}")

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval)

    def run_once(self) -> int:
        processed = 0
        for task in self.manager.list_tasks(status="pending"):
            try:
                self.manager.update_task(
                    TaskUpdate(
                        task_id=task["id"],
                        status="processed_by_ark",
                        agent="ark",
                        response=self.process_fn(task["prompt"]),
                        expected_version=task["version"],
                    )
                )
                processed += 1
            except TaskConflictError:
                continue
        return processed


if __name__ == "__main__":
    ArkWatcher(SharedTaskManager()).run_forever()
