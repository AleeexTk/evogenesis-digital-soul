"""Coordination primitives for multi-agent task processing."""

from .shared_task_manager import (
    InvalidTaskTransitionError,
    SharedTaskManager,
    TaskConflictError,
    TaskUpdate,
)
