"""OMEGA watcher: finalizes ARK-processed tasks."""

from __future__ import annotations

import time
from typing import Callable

from .shared_task_manager import SharedTaskManager, TaskConflictError, TaskUpdate


class OmegaWatcher:
    def __init__(
        self,
        manager: SharedTaskManager,
        process_fn: Callable[[str], str] | None = None,
        poll_interval: float = 0.75,
    ) -> None:
        self.manager = manager
        self.poll_interval = poll_interval
        self.process_fn = process_fn or (lambda prompt: f"OMEGA finalized: {prompt}")

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval)

    def run_once(self) -> int:
        processed = 0
        for task in self.manager.list_tasks(status="processed_by_ark"):
            try:
                started = self.manager.update_task(
                    TaskUpdate(
                        task_id=task["id"],
                        status="processing_by_omega",
                        agent="omega",
                        expected_version=task["version"],
                    )
                )
            except TaskConflictError:
                continue

            try:
                response = self.process_fn(task["prompt"])
                self.manager.update_task(
                    TaskUpdate(
                        task_id=task["id"],
                        status="complete",
                        agent="omega",
                        response=response,
                        expected_version=started["version"],
                    )
                )
                processed += 1
            except Exception as exc:
                self.manager.update_task(
                    TaskUpdate(
                        task_id=task["id"],
                        status="failed",
                        agent="omega",
                        response=str(exc),
                        expected_version=started["version"],
                    )
                )
        return processed


if __name__ == "__main__":
    OmegaWatcher(SharedTaskManager()).run_forever()
