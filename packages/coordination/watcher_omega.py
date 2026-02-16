"""Polling watcher that processes pending tasks as Omega agent."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from .shared_task_manager import SharedTaskManager, TaskConflictError


def default_omega_executor(prompt: str) -> str:
    return f"[OMEGA] Synthesis complete for: {prompt[:120]}"


def run_watcher(
    state_path: str | Path = "shared_task.json",
    poll_interval_s: float = 0.5,
    executor: Callable[[str], str] = default_omega_executor,
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
                    status="processed_by_omega",
                    event="agent.started",
                    agent_name="omega",
                )
                output = executor(task["prompt"])
                manager.update_task(
                    task["id"],
                    expected_version=current["version"],
                    status="complete",
                    event="agent.response",
                    agent_name="omega",
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
