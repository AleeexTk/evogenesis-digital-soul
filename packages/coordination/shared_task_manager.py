"""JSON-backed shared task board with optimistic concurrency and file locking."""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import fcntl


class TaskConflictError(RuntimeError):
    """Raised when task updates fail due to optimistic concurrency mismatch."""


@dataclass(frozen=True)
class TaskUpdate:
    """State transition request for one task."""

    task_id: str
    status: str
    agent: str
    response: Optional[str] = None
    expected_version: Optional[int] = None


class SharedTaskManager:
    """Manages a shared task state persisted in one JSON file."""

    def __init__(self, state_file: str | Path = "shared_task.json") -> None:
        self.state_file = Path(state_file)
        self.lock_file = self.state_file.with_suffix(self.state_file.suffix + ".lock")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self._atomic_write(self._initial_state())

    @staticmethod
    def _initial_state() -> Dict[str, Any]:
        return {
            "version": 0,
            "updated_at": time.time(),
            "tasks": [],
        }

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_file, "w", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _atomic_write(self, payload: Dict[str, Any]) -> None:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.state_file.parent, delete=False
        ) as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp.write("\n")
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = tmp.name
        os.replace(temp_path, self.state_file)

    def _load_unlocked(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return self._initial_state()
        with open(self.state_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def read_state(self) -> Dict[str, Any]:
        with self._file_lock():
            return self._load_unlocked()

    def create_task(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        with self._file_lock():
            state = self._load_unlocked()
            task = {
                "id": str(uuid.uuid4()),
                "prompt": prompt,
                "status": "pending",
                "created_at": time.time(),
                "updated_at": time.time(),
                "version": 0,
                "history": [
                    {
                        "event": "task.created",
                        "at": time.time(),
                        "metadata": metadata,
                    }
                ],
            }
            state["tasks"].append(task)
            state["version"] += 1
            state["updated_at"] = time.time()
            self._atomic_write(state)
            return task

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._file_lock():
            tasks = self._load_unlocked()["tasks"]
        if status is None:
            return tasks
        return [task for task in tasks if task["status"] == status]

    def update_task(self, update: TaskUpdate) -> Dict[str, Any]:
        with self._file_lock():
            state = self._load_unlocked()
            for task in state["tasks"]:
                if task["id"] != update.task_id:
                    continue
                if (
                    update.expected_version is not None
                    and task["version"] != update.expected_version
                ):
                    raise TaskConflictError(
                        f"Task {update.task_id} version mismatch: "
                        f"expected {update.expected_version}, got {task['version']}"
                    )
                task["status"] = update.status
                task["version"] += 1
                task["updated_at"] = time.time()
                task["history"].append(
                    {
                        "event": "agent.response",
                        "agent": update.agent,
                        "status": update.status,
                        "response": update.response,
                        "at": time.time(),
                    }
                )
                state["version"] += 1
                state["updated_at"] = time.time()
                self._atomic_write(state)
                return task

        raise KeyError(f"Task {update.task_id} not found")

    def reset(self) -> None:
        with self._file_lock():
            self._atomic_write(self._initial_state())
