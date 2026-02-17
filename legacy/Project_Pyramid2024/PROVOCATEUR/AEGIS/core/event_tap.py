from __future__ import annotations

import json
import time
import uuid
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class ExecutionEvent:
    event_id: str
    origin: str            # "llm" | "tool" | "http" | "api"
    intent: str
    provider: str
    estimated_cost: float
    latency: float
    status: str            # "allowed" | "denied" | "delayed" | "error" | "fallback"
    policy_rules: List[str]
    timestamp: str

    # Контекст
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trust_level: Optional[float] = None
    policy_mode: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class EventTap:
    """
    AEGIS Event Tap: Центральная точка логирования всех событий безопасности.
    Записывает каждое действие в NDJSON для последующего анализа.
    """
    def __init__(
        self,
        ndjson_path: str = "security_event_stream.ndjson",
        exporter: Optional[Any] = None,
    ) -> None:
        self.ndjson_path = ndjson_path
        self.exporter = exporter
        
        # Ensure log file exists
        if not os.path.exists(ndjson_path):
            with open(ndjson_path, 'w') as f:
                pass

    def record(self, event: ExecutionEvent) -> None:
        payload = asdict(event)

        # 1) Exporter (SIEM, ThreatIntel) - Optional hook
        if self.exporter:
            try:
                self.exporter.export_event(
                    event_type="execution",
                    severity="info" if event.status in ("allowed", "delayed") else "warning",
                    details=payload,
                    priority="medium",
                )
            except Exception:
                pass

        # 2) NDJSON Log
        try:
            with open(self.ndjson_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            print(f"[AEGIS] FATAL LOG ERROR: {e}")

    def log_simple(self, origin: str, intent: str, status: str, details: str):
        """Упрощенный метод логирования для быстрых событий"""
        self.record(ExecutionEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            origin=origin,
            intent=intent,
            provider="internal",
            estimated_cost=0.0,
            latency=0.0,
            status=status,
            policy_rules=["manual_log"],
            timestamp=_utc_iso(),
            meta={"details": details}
        ))

    async def aintercept(
        self,
        fn: Callable[..., Any],
        *,
        origin: str,
        provider: str,
        intent: str,
        estimated_cost: float = 0.0,
        policy_rules: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        status_on_success: str = "allowed",
        denied_reason: Optional[str] = None,
        **call_kwargs: Any,
    ) -> Any:
        """
        Async interceptor: wraps any coroutine with timing, logging, and error capture.
        Used by LLM orchestrator and Tool executor for full visibility.
        """
        start = time.time()
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        policy_rules = policy_rules or []
        ctx = context or {}

        try:
            result = await fn(**call_kwargs)
            latency = time.time() - start
            self.record(ExecutionEvent(
                event_id=event_id,
                origin=origin,
                intent=intent,
                provider=provider,
                estimated_cost=float(estimated_cost),
                latency=latency,
                status=status_on_success,
                policy_rules=policy_rules,
                timestamp=_utc_iso(),
                user_id=ctx.get("user_id"),
                session_id=ctx.get("session_id"),
                trust_level=ctx.get("trust_level"),
                policy_mode=ctx.get("policy_mode"),
                meta=ctx.get("meta"),
            ))
            return result
        except Exception as e:
            latency = time.time() - start
            meta = dict(ctx.get("meta") or {})
            meta["error"] = repr(e)
            if denied_reason:
                meta["denied_reason"] = denied_reason
            self.record(ExecutionEvent(
                event_id=event_id,
                origin=origin,
                intent=intent,
                provider=provider,
                estimated_cost=float(estimated_cost),
                latency=latency,
                status="error",
                policy_rules=policy_rules,
                timestamp=_utc_iso(),
                user_id=ctx.get("user_id"),
                session_id=ctx.get("session_id"),
                trust_level=ctx.get("trust_level"),
                policy_mode=ctx.get("policy_mode"),
                meta=meta,
            ))
            raise
