"""HTTP relay utilities for exchanging tasks/events across services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request

from packages.integration.bridge_config import BridgeConfig


class RelayError(RuntimeError):
    """Raised when relay requests fail."""


@dataclass
class RelayClient:
    """Simple API relay using Python stdlib only."""

    config: BridgeConfig
    timeout_s: int = 10

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers

    def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, data=body, headers=self._headers(), method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout_s) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RelayError(f"HTTP {exc.code} for {url}: {detail}") from exc
        except error.URLError as exc:
            raise RelayError(f"Network error for {url}: {exc}") from exc

        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}

    def send_task_to_evogenesis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.config.evogenesis_api_base.rstrip('/')}/task"
        return self._post_json(url, payload=task)

    def send_event_to_evopyramid(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.config.evopyramid_api_base.rstrip('/')}/api/events"
        return self._post_json(url, payload={"type": event_type, "payload": payload})

    def relay_task_created(self, task: Dict[str, Any], source: str = "evogenesis-digital-soul") -> Dict[str, Any]:
        envelope = {
            "source": source,
            "task_id": task.get("id"),
            "prompt": task.get("prompt"),
            "metadata": {
                "status": task.get("status"),
                "version": task.get("version"),
            },
        }
        return self.send_task_to_evogenesis(envelope)

    def relay_task_update(
        self,
        task_id: str,
        status: str,
        agent: str,
        response: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "task_id": task_id,
            "status": status,
            "agent": agent,
            "response": response,
        }
        return self.send_event_to_evopyramid(event_type="task.state.updated", payload=payload)
