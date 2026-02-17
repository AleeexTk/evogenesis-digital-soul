"""Termux connector adapter (default mock implementation)."""

from __future__ import annotations

from .protocol import ExecutionRequest, ExecutionResult


class TermuxConnector:
    """Adapter boundary for termux/edge execution."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(ok=True, output=f"termux-exec:{request.prompt}")
