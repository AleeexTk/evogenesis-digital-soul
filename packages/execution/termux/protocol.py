"""Protocol objects for execution adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionRequest:
    task_id: str
    session_id: str
    prompt: str


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    output: str
