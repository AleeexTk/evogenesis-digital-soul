"""
PROVOCATEUR/AEGIS/core/http_client.py

Controlled HTTP Client: logging, policy enforcement, caching, mocking.
Third origin ("http") in the EvoP-Security system.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    httpx = None

try:
    import requests as sync_requests
except ImportError:
    sync_requests = None

from PROVOCATEUR.AEGIS.core.event_tap import EventTap, ExecutionEvent
from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, DecisionAction


class HTTPPolicyError(PermissionError):
    """Raised when an HTTP request is denied by policy."""


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _default_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    h = dict(headers or {})
    if "User-Agent" not in {k.title(): v for k, v in h.items()}:
        h.setdefault("User-Agent", "EvoP-Security-HTTPClient/1.0")
    return h


@dataclass
class HTTPCacheEntry:
    status_code: int
    headers: Dict[str, str]
    body: bytes
    stored_at: float
    ttl_seconds: int

    def alive(self) -> bool:
        return (time.time() - self.stored_at) <= self.ttl_seconds


class HTTPClient:
    """
    Secure HTTP gateway with deterministic policy enforcement.
    
    Features:
    - Policy Gate: every request checked against PolicyEngine
    - Cache: GET responses cached with configurable TTL
    - Mock: predefined responses for testing/fallback
    - Multi-backend: httpx -> requests -> urllib fallback chain
    """

    def __init__(
        self,
        event_tap: EventTap,
        policy_engine: PolicyEngine,
        *,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 120,
        mock_responses: Optional[Dict[Tuple[str, str], Dict[str, Any]]] = None,
        timeout_seconds: float = 15.0,
    ):
        self.event_tap = event_tap
        self.policy_engine = policy_engine
        self.cache_enabled = cache_enabled
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._cache: Dict[Tuple[str, str, str], HTTPCacheEntry] = {}
        self.mock_responses = mock_responses or {}

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Any] = None,
        data: Optional[Any] = None,
        timeout_seconds: Optional[float] = None,
        # --- security context ---
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trust_level: float = 1.0,
        intent: str = "http_request",
        policy_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute HTTP request through the security pipeline.
        
        Returns normalized dict:
        {
            "status_code": int,
            "headers": dict,
            "text": str,
            "json": dict | None,
            "url": str,
            "from_cache": bool,
            "from_mock": bool
        }
        """
        method_u = (method or "GET").upper()
        host = _host_of(url)
        hdrs = _default_headers(headers)
        t0 = time.time()
        event_id = f"evt_http_{int(t0 * 1000)}"

        # --- Policy evaluation ---
        decision = self.policy_engine.evaluate({
            "origin": "http",
            "provider": host,
            "method": method_u,
            "url": url,
            "intent": intent,
            "user_id": user_id,
            "session_id": session_id,
            "trust_level": trust_level,
            "policy_mode": policy_mode,
        })

        # Forced delay
        if decision.action == DecisionAction.DELAY and decision.delay_seconds:
            await asyncio.sleep(decision.delay_seconds)

        # Denial
        if decision.action == DecisionAction.DENY:
            self._record_event(event_id, intent, host, 0.0, "denied", [decision.reason])
            raise HTTPPolicyError(decision.reason)

        # Fallback (cache / mock)
        if decision.action == DecisionAction.FALLBACK:
            resp = self._fallback_response(method_u, url)
            self._record_event(event_id, intent, host, time.time() - t0, "fallback", [decision.reason])
            return resp

        # --- Cache for GET ---
        if self.cache_enabled and method_u == "GET":
            cache_key = (method_u, url, json.dumps(params or {}, sort_keys=True))
            cached = self._cache.get(cache_key)
            if cached and cached.alive():
                self._record_event(event_id, intent, host, time.time() - t0, "allowed", ["cache_hit"])
                return self._normalize_cached(url, cached)

        # --- Real request ---
        try:
            resp = await self._do_request(
                method_u, url,
                params=params, headers=hdrs,
                json_body=json_body, data=data,
                timeout_seconds=timeout_seconds or self.timeout_seconds,
            )
            latency = time.time() - t0
            self._record_event(event_id, intent, host, latency, "allowed", [decision.reason])

            # Store in cache
            if self.cache_enabled and method_u == "GET":
                cache_key = (method_u, url, json.dumps(params or {}, sort_keys=True))
                self._cache[cache_key] = HTTPCacheEntry(
                    status_code=resp["status_code"],
                    headers=resp.get("headers", {}),
                    body=resp.get("_body_bytes", b""),
                    stored_at=time.time(),
                    ttl_seconds=self.cache_ttl_seconds,
                )
            resp.pop("_body_bytes", None)
            return resp
        except HTTPPolicyError:
            raise
        except Exception as e:
            latency = time.time() - t0
            self._record_event(event_id, intent, host, latency, "error", [f"exception:{type(e).__name__}"])
            raise

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        return await self.request("POST", url, **kwargs)

    # ---------- Private ----------

    def _record_event(self, event_id: str, intent: str, provider: str,
                      latency: float, status: str, policy_rules: list) -> None:
        self.event_tap.record(ExecutionEvent(
            event_id=event_id,
            origin="http",
            intent=intent,
            provider=provider or "unknown",
            estimated_cost=0.0,
            latency=latency,
            status=status,
            policy_rules=policy_rules,
            timestamp=_utc_iso(),
        ))

    def _fallback_response(self, method: str, url: str) -> Dict[str, Any]:
        # 1) Exact mock match
        mock = self.mock_responses.get((method, url))
        if mock:
            return self._normalize_mock(url, mock)

        # 2) Cache (GET only)
        if self.cache_enabled and method == "GET":
            cache_key = (method, url, json.dumps({}, sort_keys=True))
            cached = self._cache.get(cache_key)
            if cached and cached.alive():
                return self._normalize_cached(url, cached)

        # 3) Safe fallback
        return {
            "status_code": 599,
            "headers": {},
            "text": "",
            "json": None,
            "url": url,
            "from_cache": False,
            "from_mock": False,
        }

    def _normalize_cached(self, url: str, cached: HTTPCacheEntry) -> Dict[str, Any]:
        body = cached.body or b""
        text = body.decode("utf-8", errors="replace")
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            pass
        return {
            "status_code": cached.status_code,
            "headers": cached.headers,
            "text": text,
            "json": parsed,
            "url": url,
            "from_cache": True,
            "from_mock": False,
        }

    def _normalize_mock(self, url: str, mock: Dict[str, Any]) -> Dict[str, Any]:
        status = int(mock.get("status_code", 200))
        headers = dict(mock.get("headers", {}))
        if "json" in mock:
            text = json.dumps(mock["json"])
            parsed = mock["json"]
        elif "text" in mock:
            text = str(mock["text"])
            parsed = None
        else:
            text = ""
            parsed = None
        return {
            "status_code": status,
            "headers": headers,
            "text": text,
            "json": parsed,
            "url": url,
            "from_cache": False,
            "from_mock": True,
        }

    async def _do_request(
        self, method: str, url: str, *,
        params: Optional[Dict], headers: Dict[str, str],
        json_body: Optional[Any], data: Optional[Any],
        timeout_seconds: float,
    ) -> Dict[str, Any]:
        # 1) httpx (async, preferred)
        if httpx is not None:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                r = await client.request(
                    method, url, params=params, headers=headers,
                    json=json_body, data=data
                )
                body = r.content or b""
                text = body.decode("utf-8", errors="replace")
                parsed = None
                try:
                    parsed = r.json()
                except Exception:
                    pass
                return {
                    "status_code": r.status_code,
                    "headers": dict(r.headers),
                    "text": text,
                    "json": parsed,
                    "url": str(r.url),
                    "_body_bytes": body,
                }

        # 2) requests (sync -> thread)
        if sync_requests is not None:
            def _sync_req():
                r = sync_requests.request(
                    method, url, params=params, headers=headers,
                    json=json_body, data=data, timeout=timeout_seconds
                )
                body = r.content or b""
                text = body.decode("utf-8", errors="replace")
                parsed = None
                try:
                    parsed = r.json()
                except Exception:
                    pass
                return {
                    "status_code": r.status_code,
                    "headers": dict(r.headers),
                    "text": text,
                    "json": parsed,
                    "url": r.url,
                    "_body_bytes": body,
                }
            return await asyncio.to_thread(_sync_req)

        # 3) urllib (sync -> thread, last resort)
        import urllib.request
        import urllib.parse

        def _sync_urllib():
            q = urllib.parse.urlencode(params or {})
            full = url if not q else f"{url}?{q}"
            payload = None
            if json_body is not None:
                payload = json.dumps(json_body).encode("utf-8")
                headers["Content-Type"] = "application/json"
            elif data is not None:
                if isinstance(data, (bytes, bytearray)):
                    payload = bytes(data)
                else:
                    payload = str(data).encode("utf-8")
            req = urllib.request.Request(full, data=payload, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                body = resp.read() or b""
                text = body.decode("utf-8", errors="replace")
                parsed = None
                try:
                    parsed = json.loads(text)
                except Exception:
                    pass
                return {
                    "status_code": getattr(resp, "status", 200),
                    "headers": dict(resp.headers.items()),
                    "text": text,
                    "json": parsed,
                    "url": full,
                    "_body_bytes": body,
                }

        return await asyncio.to_thread(_sync_urllib)
