"""
EvoP-Security Test Suite: Trust-Aware Wallet
Verifies credit consumption and automatic freezing on low trust.
"""
import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PROVOCATEUR.AEGIS.core.wallet_manager import WalletManager
from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, DecisionAction

def test_wallet_basic_consumption():
    wallet = WalletManager(initial_balance=100.0)
    
    # 1. Successful spend
    user_alpha = "user_alpha"
    success = wallet.request_funds(10.0, trust_level=1.0, user_id=user_alpha)
    assert success is True
    status = wallet.get_status(user_alpha)
    assert status["balance"] == 90.0
    print("[PASS] Basic consumption (Multi-user)")

def test_wallet_trust_freeze():
    wallet = WalletManager(initial_balance=100.0, trust_threshold=0.5)
    user_beta = "user_beta"
    
    # 1. Low trust should freeze specific user
    success = wallet.request_funds(5.0, trust_level=0.1, user_id=user_beta)
    assert success is False
    status = wallet.get_status(user_beta)
    assert status["is_frozen"] is True
    
    # 2. Other user remains unfrozen
    status_alpha = wallet.get_status("user_alpha")
    assert status_alpha["is_frozen"] is False
    print("[PASS] Trust-based freeze (Isolation)")

def test_wallet_policy_integration():
    wallet = WalletManager(initial_balance=0.5) # insufficient
    engine = PolicyEngine(rules={
        "deny": [
            {"condition": {"wallet_balance": {"lt": 1.0}}, "reason": "No money"}
        ]
    })
    
    status = wallet.get_status("anonymous")
    ctx = {
        "wallet_balance": status["balance"],
        "is_frozen": status["is_frozen"]
    }
    
    decision = engine.evaluate(ctx)
    assert decision.action == DecisionAction.DENY
    print("[PASS] Policy integration (Bankupt context)")

if __name__ == "__main__":
    test_wallet_basic_consumption()
    test_wallet_trust_freeze()
    test_wallet_policy_integration()
    print("\n[COMPLETE] All Wallet tests passed!")
