"""Shared task state manager with atomic writes and optimistic concurrency."""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskConflictError(RuntimeError):
    """Raised when a task update is attempted with a stale version."""


class SharedTaskManager:
    """Manage task state in a JSON file for local multi-agent coordination."""

    def __init__(self, state_path: str | Path = "shared_task.json") -> None:
        self.state_path = Path(state_path)
        self.lock_path = self.state_path.with_suffix(self.state_path.suffix + ".lock")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._write_state({"tasks": [], "updated_at": self._now()})

    @staticmethod
    def _now() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @contextmanager
    def _file_lock(self, timeout_s: float = 5.0, poll_s: float = 0.05):
        start = time.time()
        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                if time.time() - start > timeout_s:
                    raise TimeoutError(f"Unable to acquire lock: {self.lock_path}")
                time.sleep(poll_s)
        try:
            yield
        finally:
            try:
                os.unlink(self.lock_path)
            except FileNotFoundError:
                pass

    def _read_state(self) -> Dict[str, Any]:
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_state(self, state: Dict[str, Any]) -> None:
        data = json.dumps(state, ensure_ascii=False, indent=2)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.state_path.parent, delete=False
        ) as tmp:
            tmp.write(data)
            tmp_name = tmp.name
        os.replace(tmp_name, self.state_path)

    def list_tasks(self) -> List[Dict[str, Any]]:
        with self._file_lock():
            return self._read_state().get("tasks", [])

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._file_lock():
            for task in self._read_state().get("tasks", []):
                if task["id"] == task_id:
                    return task
        return None

    def create_task(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._file_lock():
            state = self._read_state()
            task = {
                "id": str(uuid.uuid4()),
                "prompt": prompt,
                "metadata": metadata or {},
                "status": "pending",
                "version": 1,
                "created_at": self._now(),
                "updated_at": self._now(),
                "history": [{"event": "task.created", "at": self._now()}],
                "agent_outputs": {},
            }
            state["tasks"].append(task)
            state["updated_at"] = self._now()
            self._write_state(state)
            return task

    def update_task(
        self,
        task_id: str,
        *,
        expected_version: Optional[int] = None,
        status: Optional[str] = None,
        event: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._file_lock():
            state = self._read_state()
            tasks = state.get("tasks", [])
            for idx, task in enumerate(tasks):
                if task["id"] != task_id:
                    continue

                if expected_version is not None and task["version"] != expected_version:
                    raise TaskConflictError(
                        f"Stale version: expected={expected_version} actual={task['version']}"
                    )

                if status:
                    task["status"] = status
                if agent_name and agent_output is not None:
                    task["agent_outputs"][agent_name] = agent_output

                task["version"] += 1
                task["updated_at"] = self._now()
                if event:
                    entry = {"event": event, "at": self._now()}
                    if agent_name:
                        entry["agent"] = agent_name
                    task["history"].append(entry)

                tasks[idx] = task
                state["updated_at"] = self._now()
                self._write_state(state)
                return task

        raise KeyError(f"Task not found: {task_id}")

    def reset(self) -> None:
        with self._file_lock():
            self._write_state({"tasks": [], "updated_at": self._now()})
