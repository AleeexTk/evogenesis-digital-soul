"""Polling watcher that processes pending tasks as Ark agent."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from .shared_task_manager import SharedTaskManager, TaskConflictError


def default_ark_executor(prompt: str) -> str:
    return f"[ARK] Analysis complete for: {prompt[:120]}"


def run_watcher(
    state_path: str | Path = "shared_task.json",
    poll_interval_s: float = 0.5,
    executor: Callable[[str], str] = default_ark_executor,
) -> None:
    manager = SharedTaskManager(state_path)
    while True:
        tasks = manager.list_tasks()
        pending = [t for t in tasks if t.get("status") == "pending"]
        for task in pending:
            try:
                current = manager.update_task(
                    task["id"],
                    expected_version=task["version"],
                    status="processed_by_ark",
                    event="agent.started",
                    agent_name="ark",
                )
                output = executor(task["prompt"])
                manager.update_task(
                    task["id"],
                    expected_version=current["version"],
                    status="complete",
                    event="agent.response",
                    agent_name="ark",
                    agent_output=output,
                )
                manager.update_task(task["id"], event="task.completed")
            except TaskConflictError:
                continue
            except Exception:
                manager.update_task(task["id"], status="failed", event="task.failed")
        time.sleep(poll_interval_s)


if __name__ == "__main__":
    run_watcher()
