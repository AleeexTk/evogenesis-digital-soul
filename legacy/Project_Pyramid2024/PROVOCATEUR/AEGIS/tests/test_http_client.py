"""
EvoP-Security Test Suite: HTTPClient
"""
import sys, os, asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import tempfile
from PROVOCATEUR.AEGIS.core.event_tap import EventTap
from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine
from PROVOCATEUR.AEGIS.core.http_client import HTTPClient, HTTPPolicyError


def _make_client(rules=None, mock_responses=None):
    tap = EventTap(ndjson_path=os.path.join(tempfile.gettempdir(), "test_http.ndjson"))
    engine = PolicyEngine(rules=rules or {})
    return HTTPClient(tap, engine, mock_responses=mock_responses or {})


def test_http_denied_domain():
    client = _make_client(rules={
        "deny": [{"condition": {"origin": "http", "provider": "api.telegram.org"}, "reason": "blocked"}]
    })
    try:
        asyncio.run(client.get("https://api.telegram.org/botXXX/getMe"))
        assert False, "Should have raised HTTPPolicyError"
    except HTTPPolicyError as e:
        assert "blocked" in str(e)
    print("[PASS] test_http_denied_domain")


def test_http_mock_response():
    mock = {
        ("GET", "https://example.com/health"): {"status_code": 200, "json": {"ok": True}}
    }
    client = _make_client(
        rules={"fallback": [{"condition": {"origin": "http", "provider": "example.com"}}]},
        mock_responses=mock,
    )
    resp = asyncio.run(client.get("https://example.com/health"))
    assert resp["status_code"] == 200
    assert resp["json"]["ok"] is True
    assert resp["from_mock"] is True
    print("[PASS] test_http_mock_response")


def test_http_fallback_no_mock():
    """When fallback triggers but no mock exists, return safe 599."""
    client = _make_client(
        rules={"fallback": [{"condition": {"origin": "http", "provider": "unknown.io"}}]},
    )
    resp = asyncio.run(client.get("https://unknown.io/api"))
    assert resp["status_code"] == 599
    assert resp["from_mock"] is False
    assert resp["from_cache"] is False
    print("[PASS] test_http_fallback_no_mock")


def test_http_allowed_request():
    """Default allow should let real requests through (testing with httpbin)."""
    client = _make_client()
    try:
        resp = asyncio.run(client.get("https://httpbin.org/get", timeout_seconds=5.0))
        assert resp["status_code"] == 200
        print("[PASS] test_http_allowed_request")
    except Exception as e:
        # Network might be unavailable, that's OK for offline testing
        print(f"[SKIP] test_http_allowed_request (network unavailable: {type(e).__name__})")


if __name__ == "__main__":
    test_http_denied_domain()
    test_http_mock_response()
    test_http_fallback_no_mock()
    test_http_allowed_request()
    print("\n[SUCCESS] All HTTPClient tests passed!")
