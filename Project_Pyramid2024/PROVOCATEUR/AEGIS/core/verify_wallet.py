import sys
import os
import time

# Add roots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PROVOCATEUR.AEGIS.core.wallet_manager import WalletManager

def test_wallet():
    wm = WalletManager(initial_balance=100.0, trust_threshold=0.3)
    
    print("--- Test 1: Basic Expenditure ---")
    success = wm.request_funds(10.0, 0.8, user_id="user_alpha")
    status = wm.get_status("user_alpha")
    print(f"User Alpha: Success={success}, Balance={status['balance']}, Consumed={status['consumed']}")
    assert success == True
    assert status['balance'] == 90.0

    print("\n--- Test 2: Multi-User Isolation ---")
    status_beta = wm.get_status("user_beta")
    print(f"User Beta initial balance: {status_beta['balance']}")
    assert status_beta['balance'] == 100.0
    
    wm.request_funds(50.0, 0.8, user_id="user_beta")
    print(f"User Beta after spending 50: {wm.get_status('user_beta')['balance']}")
    print(f"User Alpha balance remains: {wm.get_status('user_alpha')['balance']}")
    assert wm.get_status('user_alpha')['balance'] == 90.0

    print("\n--- Test 3: Trust-Based Freeze ---")
    # Drop trust for Beta
    success = wm.request_funds(1.0, 0.1, user_id="user_beta")
    status_beta = wm.get_status("user_beta")
    print(f"User Beta (Low Trust): Success={success}, Internal Frozen={status_beta['is_frozen']}")
    assert success == False
    assert status_beta['is_frozen'] == True
    
    # Check Alpha - should NOT be frozen
    status_alpha = wm.get_status("user_alpha")
    print(f"User Alpha Frozen status: {status_alpha['is_frozen']}")
    assert status_alpha['is_frozen'] == False
    
    # Try Alpha spend - should succeed
    success = wm.request_funds(1.0, 0.8, user_id="user_alpha")
    print(f"User Alpha spend success: {success}")
    assert success == True

    print("\n--- Test 4: Grant Credits & total_granted ---")
    wm.grant_credits(50.0, user_id="user_alpha")
    status_alpha = wm.get_status("user_alpha")
    print(f"User Alpha Total Granted: {status_alpha['total_granted']}, Current Balance: {status_alpha['balance']}")
    assert status_alpha['total_granted'] == 150.0
    assert status_alpha['balance'] == 139.0

    print("\n[VERIFICATION SUCCESSFUL]")

if __name__ == "__main__":
    test_wallet()
