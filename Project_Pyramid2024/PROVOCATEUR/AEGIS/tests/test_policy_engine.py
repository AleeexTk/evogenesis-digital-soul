"""
EvoP-Security Test Suite: PolicyEngine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, DecisionAction


def test_deny_tool_destructive():
    engine = PolicyEngine(rules={
        "deny": [{"condition": {"origin": "tool", "intent": "destructive"}, "reason": "blocked"}]
    })
    d = engine.evaluate({"origin": "tool", "intent": "destructive"})
    assert d.action == DecisionAction.DENY
    print("[PASS] test_deny_tool_destructive")


def test_allow_safe_tool():
    engine = PolicyEngine(rules={
        "deny": [{"condition": {"origin": "tool", "intent": "destructive"}}]
    })
    d = engine.evaluate({"origin": "tool", "intent": "read_only"})
    assert d.action == DecisionAction.ALLOW
    print("[PASS] test_allow_safe_tool")


def test_fallback_low_trust_openai():
    engine = PolicyEngine(rules={
        "fallback": [{
            "condition": {"origin": "llm", "provider": {"in": ["openai"]}},
            "modified_params": {"provider": "ollama"}
        }]
    })
    d = engine.evaluate({"origin": "llm", "provider": "openai"})
    assert d.action == DecisionAction.FALLBACK
    assert d.modified_params["provider"] == "ollama"
    print("[PASS] test_fallback_low_trust_openai")


def test_delay_low_trust():
    engine = PolicyEngine(rules={
        "delay": [{
            "condition": {"trust_level": {"lt": 0.3}},
            "delay_seconds": 1.5
        }]
    })
    d = engine.evaluate({"trust_level": 0.1})
    assert d.action == DecisionAction.DELAY
    assert d.delay_seconds == 1.5
    print("[PASS] test_delay_low_trust")


def test_deny_http_domain():
    engine = PolicyEngine(rules={
        "deny": [{"condition": {"origin": "http", "provider": "api.telegram.org"}, "reason": "blocked"}]
    })
    d = engine.evaluate({"origin": "http", "provider": "api.telegram.org"})
    assert d.action == DecisionAction.DENY
    print("[PASS] test_deny_http_domain")


def test_compound_condition():
    """Test condition with multiple fields (AND logic)."""
    engine = PolicyEngine(rules={
        "deny": [{
            "condition": {"origin": "llm", "trust_level": {"lt": 0.4}, "provider": {"in": ["openai"]}},
            "reason": "low trust + expensive provider"
        }]
    })
    # Should deny: low trust + openai
    d = engine.evaluate({"origin": "llm", "trust_level": 0.2, "provider": "openai"})
    assert d.action == DecisionAction.DENY

    # Should allow: low trust but local provider (not in list)
    d = engine.evaluate({"origin": "llm", "trust_level": 0.2, "provider": "ollama"})
    assert d.action == DecisionAction.ALLOW

    # Should allow: openai but high trust
    d = engine.evaluate({"origin": "llm", "trust_level": 0.9, "provider": "openai"})
    assert d.action == DecisionAction.ALLOW
    print("[PASS] test_compound_condition")


def test_state_locked_tool():
    """Test that tools are denied when not in PLANNING/EXECUTING states."""
    engine = PolicyEngine(rules={
        "deny": [{
            "condition": {"origin": "tool", "state": {"not_in": ["PLANNING", "EXECUTING"]}},
            "reason": "STATE LOCK"
        }]
    })
    
    # 1. Deny in IDLE
    d = engine.evaluate({"origin": "tool", "state": "IDLE"})
    assert d.action == DecisionAction.DENY
    assert d.reason == "STATE LOCK"
    
    # 2. Allow in EXECUTING
    d = engine.evaluate({"origin": "tool", "state": "EXECUTING"})
    assert d.action == DecisionAction.ALLOW
    print("[PASS] test_state_locked_tool")


if __name__ == "__main__":
    test_deny_tool_destructive()
    test_allow_safe_tool()
    test_fallback_low_trust_openai()
    test_delay_low_trust()
    test_deny_http_domain()
    test_compound_condition()
    test_state_locked_tool()
    print("\n[SUCCESS] All PolicyEngine tests passed!")
