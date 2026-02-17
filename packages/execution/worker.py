"""Execution worker that processes pending tasks via execution adapter."""

from __future__ import annotations

import time
from typing import Optional

from packages.coordination.shared_task_manager import SharedTaskManager, TaskConflictError, TaskUpdate
from packages.execution.termux.connector import TermuxConnector
from packages.execution.termux.protocol import ExecutionRequest
from packages.integration.relay import RelayClient, RelayError


class ExecutionWorker:
    def __init__(
        self,
        manager: SharedTaskManager,
        connector: Optional[TermuxConnector] = None,
        relay: Optional[RelayClient] = None,
        poll_interval: float = 0.75,
    ) -> None:
        self.manager = manager
        self.connector = connector or TermuxConnector()
        self.relay = relay
        self.poll_interval = poll_interval

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval)

    def _safe_relay_update(self, task_id: str, status: str, agent: str, response: str) -> None:
        if not self.relay:
            return
        try:
            self.relay.relay_task_update(task_id=task_id, status=status, agent=agent, response=response)
        except RelayError:
            return

    def run_once(self) -> int:
        processed = 0
        for task in self.manager.list_tasks(status="pending"):
            try:
                started = self.manager.update_task(
                    TaskUpdate(
                        task_id=task["id"],
                        status="processing_by_exec",
                        agent="execution",
                        expected_version=task["version"],
                    )
                )
            except TaskConflictError:
                continue

            request = ExecutionRequest(
                task_id=task["id"],
                session_id=task.get("session_id", ""),
                prompt=task["prompt"],
            )
            result = self.connector.execute(request)
            final_status = "done" if result.ok else "failed"
            updated = self.manager.update_task(
                TaskUpdate(
                    task_id=task["id"],
                    status=final_status,
                    agent="execution",
                    response=result.output,
                    expected_version=started["version"],
                )
            )
            self._safe_relay_update(
                task_id=updated["id"],
                status=updated["status"],
                agent="execution",
                response=result.output,
            )
            processed += 1
        return processed
