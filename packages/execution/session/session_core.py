"""Session helpers for execution layer."""

from __future__ import annotations

import uuid


def generate_session_id() -> str:
    return str(uuid.uuid4())
