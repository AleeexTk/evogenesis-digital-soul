"""
PROVOCATEUR/AEGIS/core/wallet_manager.py

Trust-Aware Wallet Manager.
Manages credits and budget based on Trust Scores.
"""

import time
from typing import Any, Dict, Optional


class WalletManager:
    """
    Stateful manager for API/Token credits.
    Integrates with Trust Scores to freeze or grant assets.
    Supports multiple users.
    """

    def __init__(self, initial_balance: float = 1000.0, trust_threshold: float = 0.3):
        self.initial_balance = initial_balance
        self.trust_threshold = trust_threshold
        # Per-user state: { user_id: { balance, consumed, total_granted, is_frozen, last_update } }
        self.users: Dict[str, Dict[str, Any]] = {}

    def _ensure_user(self, user_id: str):
        """Initialize user state if not exists."""
        if user_id not in self.users:
            self.users[user_id] = {
                "balance": self.initial_balance,
                "consumed": 0.0,
                "total_granted": self.initial_balance,
                "is_frozen": False,
                "last_update": time.time()
            }

    def get_status(self, user_id: str = "anonymous") -> Dict[str, Any]:
        """Returns the current wallet status for a specific user."""
        self._ensure_user(user_id)
        u = self.users[user_id]
        return {
            "user_id": user_id,
            "balance": round(u["balance"], 2),
            "consumed": round(u["consumed"], 2),
            "total_granted": round(u["total_granted"], 2),
            "is_frozen": u["is_frozen"],
            "can_spend": u["balance"] > 0 and not u["is_frozen"]
        }

    def request_funds(self, amount: float, trust_level: float, user_id: str = "anonymous") -> bool:
        """
        Check if funds can be spent for a specific user.
        If trust is too low, the user's wallet freezes automatically.
        """
        self._ensure_user(user_id)
        u = self.users[user_id]

        # Security Trigger: Instant freeze if trust drops below threshold
        if trust_level < self.trust_threshold:
            u["is_frozen"] = True
            return False

        if u["is_frozen"]:
            return False

        if u["balance"] < amount:
            return False

        # Spend
        u["balance"] -= amount
        u["consumed"] += amount
        u["last_update"] = time.time()
        return True

    def grant_credits(self, amount: float, user_id: str = "anonymous"):
        """Add credits to a user's wallet."""
        self._ensure_user(user_id)
        u = self.users[user_id]
        u["balance"] += amount
        u["total_granted"] += amount
        u["last_update"] = time.time()

    def set_freeze(self, status: bool, user_id: str = "anonymous"):
        """Manually freeze or unfreeze assets for a user."""
        self._ensure_user(user_id)
        self.users[user_id]["is_frozen"] = status
        self.users[user_id]["last_update"] = time.time()
