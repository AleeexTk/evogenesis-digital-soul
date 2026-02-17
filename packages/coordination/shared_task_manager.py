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

try:
    import fcntl  # type: ignore
except ImportError:  # pragma: no cover - windows fallback
    fcntl = None
    import msvcrt  # type: ignore


class TaskConflictError(RuntimeError):
    """Raised when task updates fail due to optimistic concurrency mismatch."""


class InvalidTaskTransitionError(RuntimeError):
    """Raised when task transition is not allowed by the state machine."""


@dataclass(frozen=True)
class TaskUpdate:
    """State transition request for one task."""

    task_id: str
    status: str
    agent: str
    response: Optional[str] = None
    expected_version: Optional[int] = None
    event_type: Optional[str] = None


ALLOWED_TRANSITIONS = {
    "pending": {"processing_by_ark", "processed_by_ark", "processing_by_exec", "failed"},
    "processing_by_ark": {"processed_by_ark", "failed"},
    "processed_by_ark": {"processing_by_omega", "processing_by_exec", "complete", "done", "failed"},
    "processing_by_omega": {"complete", "done", "failed"},
    "processing_by_exec": {"done", "complete", "failed"},
    "complete": set(),
    "done": set(),
    "failed": set(),
}


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
        return {"version": 0, "updated_at": time.time(), "tasks": []}

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_file, "a+", encoding="utf-8") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            else:  # pragma: no cover
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                else:  # pragma: no cover
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

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

    @staticmethod
    def _append_history(task: Dict[str, Any], event_type: str, **fields: Any) -> None:
        task["history"].append(
            {"event": event_type, "event_id": str(uuid.uuid4()), "at": time.time(), **fields}
        )

    def create_task(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        with self._file_lock():
            state = self._load_unlocked()
            now = time.time()
            task = {
                "id": str(uuid.uuid4()),
                "session_id": metadata.get("session_id", str(uuid.uuid4())),
                "prompt": prompt,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
                "version": 0,
                "state_version": state["version"] + 1,
                "history": [],
            }
            self._append_history(task, "task.created", metadata=metadata)
            state["tasks"].append(task)
            state["version"] += 1
            state["updated_at"] = now
            self._atomic_write(state)
            return task

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._file_lock():
            tasks = self._load_unlocked()["tasks"]
        if status is None:
            return tasks
        return [task for task in tasks if task["status"] == status]

    @staticmethod
    def _validate_transition(old_status: str, new_status: str) -> None:
        if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise InvalidTaskTransitionError(f"Invalid transition: {old_status} -> {new_status}")

    @staticmethod
    def _default_event_for_status(status: str) -> str:
        if status in {"complete", "done"}:
            return "task.completed"
        if status == "failed":
            return "task.failed"
        if status.startswith("processing_by_"):
            return "agent.started"
        return "agent.response"

    def update_task(self, update: TaskUpdate) -> Dict[str, Any]:
        with self._file_lock():
            state = self._load_unlocked()
            now = time.time()
            for task in state["tasks"]:
                if task["id"] != update.task_id:
                    continue
                if update.expected_version is not None and task["version"] != update.expected_version:
                    raise TaskConflictError(
                        f"Task {update.task_id} version mismatch: expected {update.expected_version}, got {task['version']}"
                    )

                self._validate_transition(task["status"], update.status)
                task["status"] = update.status
                task["version"] += 1
                task["state_version"] = state["version"] + 1
                task["updated_at"] = now
                self._append_history(
                    task,
                    update.event_type or self._default_event_for_status(update.status),
                    agent=update.agent,
                    status=update.status,
                    response=update.response,
                )
                state["version"] += 1
                state["updated_at"] = now
                self._atomic_write(state)
                return task

        raise KeyError(f"Task {update.task_id} not found")

    def reset(self) -> None:
        with self._file_lock():
            self._atomic_write(self._initial_state())
