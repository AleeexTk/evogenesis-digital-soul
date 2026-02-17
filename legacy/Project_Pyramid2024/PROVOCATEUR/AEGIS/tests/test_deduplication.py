"""
EvoP-Security Test Suite: Deduplication + Loop Protection
"""
import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, DecisionAction
from PROVOCATEUR.AEGIS.core.deduplication_engine import DeduplicationEngine


def test_loop_detection_flow():
    # 1. Setup engine with loop policy
    engine = PolicyEngine(rules={
        "deny": [
            {
                "condition": {"loop_count": {"gt": 3}},
                "reason": "Loop detected"
            }
        ]
    })
    dedup = DeduplicationEngine(window_size=10, ttl_seconds=5)
    
    ctx = {
        "origin": "llm",
        "intent": "repeated_action",
        "provider": "openai",
        "params": {"q": "Hello"}
    }
    
    # 2. Run the same call 5 times
    for i in range(1, 6):
        count = dedup.check_and_record(ctx)
        # Update ctx with loop count for PolicyEngine
        ctx["loop_count"] = count
        
        decision = engine.evaluate(ctx)
        
        if i <= 3:
            assert decision.action == DecisionAction.ALLOW, f"Call {i} should be allowed"
            print(f"[PASS] Call {i}: ALLOWED (count={count})")
        else:
            assert decision.action == DecisionAction.DENY, f"Call {i} should be denied"
            assert "Loop detected" in decision.reason
            print(f"[PASS] Call {i}: DENIED (count={count})")

    print("[SUCCESS] test_loop_detection_flow passed!")


def test_fingerprint_distinctness():
    dedup = DeduplicationEngine()
    
    ctx1 = {"origin": "tool", "intent": "read", "params": {"file": "a.txt"}}
    ctx2 = {"origin": "tool", "intent": "read", "params": {"file": "b.txt"}}
    
    c1 = dedup.check_and_record(ctx1)
    c2 = dedup.check_and_record(ctx2)
    c3 = dedup.check_and_record(ctx1)
    
    assert c1 == 1
    assert c2 == 1
    assert c3 == 2
    print("[PASS] test_fingerprint_distinctness")


if __name__ == "__main__":
    test_loop_detection_flow()
    test_fingerprint_distinctness()
    print("\n[COMPLETE] All Deduplication tests passed!")
