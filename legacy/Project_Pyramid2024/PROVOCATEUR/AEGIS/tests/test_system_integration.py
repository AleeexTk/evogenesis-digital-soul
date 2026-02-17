import sys
import os
import asyncio
import time
import json
from datetime import datetime

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, BASE_DIR)

from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, DecisionAction
from PROVOCATEUR.AEGIS.core.event_tap import EventTap
from PROVOCATEUR.AEGIS.core.http_client import HTTPClient, HTTPPolicyError

LOG_PATH = os.path.join(BASE_DIR, "integration_audit.ndjson")

def cleanup():
    if os.path.exists(LOG_PATH):
        try:
            os.remove(LOG_PATH)
        except:
            pass

async def test_proven_circulation():
    print("\n--- Test 1: Proven Circulation (Happy Path) ---")
    print(f"DEBUG: LOG_PATH is {LOG_PATH}")
    cleanup()
    print("DEBUG: Cleanup done")
    tap = EventTap(ndjson_path=LOG_PATH)
    print("DEBUG: EventTap initialized")
    engine = PolicyEngine(rules={"deny": [{"condition": {"provider": "evil.com"}, "reason": "block malicious"}]})
    print("DEBUG: PolicyEngine initialized")
    client = HTTPClient(event_tap=tap, policy_engine=engine)
    print("DEBUG: HTTPClient initialized")
    client.mock_responses = {("GET", "https://example.com"): {"status_code": 200, "text": "OK"}}
    
    await client.get("https://example.com", intent="integration_test")
    
    # Check NDJSON
    assert os.path.exists(LOG_PATH), "Log file was not created"
    with open(LOG_PATH, "r") as f:
        events = [json.loads(line) for line in f]
    
    assert len(events) > 0
    assert events[-1]["provider"] == "example.com"
    print("[PASS] Circulation proven via NDJSON logs.")

async def test_runtime_enforcement_deny():
    print("\n--- Test 2: Runtime Enforcement (DENY) ---")
    tap = EventTap(ndjson_path=LOG_PATH)
    engine = PolicyEngine(rules={"deny": [{"condition": {"provider": "evil.com"}, "reason": "SECURITY_BLOCK"}]})
    client = HTTPClient(event_tap=tap, policy_engine=engine)
    
    try:
        await client.get("https://evil.com")
        assert False, "Should have raised HTTPPolicyError"
    except HTTPPolicyError as e:
        assert "SECURITY_BLOCK" in str(e)
        print(f"[PASS] Runtime blocked execution: {e}")

    with open(LOG_PATH, "r") as f:
        log_content = f.read()
    assert "denied" in log_content
    assert "evil.com" in log_content

async def test_runtime_enforcement_delay():
    print("\n--- Test 3: Runtime Enforcement (DELAY) ---")
    tap = EventTap(ndjson_path=LOG_PATH)
    engine = PolicyEngine(rules={"delay": [{"condition": {"provider": "slow.com"}, "delay_seconds": 1.0}]})
    client = HTTPClient(event_tap=tap, policy_engine=engine)
    client.mock_responses = {("GET", "https://slow.com"): {"status_code": 200}}
    
    t0 = time.time()
    await client.get("https://slow.com")
    elapsed = time.time() - t0
    
    assert elapsed >= 1.0
    print(f"[PASS] Runtime enforced delay: {elapsed:.2f}s")

async def test_boundary_empty_policy():
    print("\n--- Test 4: Boundary Condition (Empty Policy) ---")
    cleanup()
    tap = EventTap(ndjson_path=LOG_PATH)
    engine = PolicyEngine(rules={}) 
    client = HTTPClient(event_tap=tap, policy_engine=engine)
    client.mock_responses = {("GET", "https://any.com"): {"status_code": 200}}
    
    resp = await client.get("https://any.com")
    assert resp["status_code"] == 200
    print("[PASS] Empty policy defaults to ALLOW.")

async def run_all():
    try:
        await test_proven_circulation()
        await test_runtime_enforcement_deny()
        await test_runtime_enforcement_delay()
        await test_boundary_empty_policy()
        print("\n[COMPLETE] All Integration Tests Passed!")
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Test failed with: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        cleanup()

if __name__ == "__main__":
    asyncio.run(run_all())
