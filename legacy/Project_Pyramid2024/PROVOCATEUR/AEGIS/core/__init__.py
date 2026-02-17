"""
PROVOCATEUR/AEGIS/core — EvoP-Security Package

Deterministic security layer for LLM agents.
Three origins of control: LLM, Tools, HTTP.
"""

from PROVOCATEUR.AEGIS.core.event_tap import EventTap, ExecutionEvent
from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, PolicyDecision, DecisionAction
from PROVOCATEUR.AEGIS.core.http_client import HTTPClient, HTTPPolicyError
from PROVOCATEUR.AEGIS.core.deduplication_engine import DeduplicationEngine
from PROVOCATEUR.AEGIS.core.wallet_manager import WalletManager

__all__ = [
    "EventTap",
    "ExecutionEvent",
    "PolicyEngine",
    "PolicyDecision",
    "DecisionAction",
    "HTTPClient",
    "HTTPPolicyError",
    "DeduplicationEngine",
    "WalletManager",
]
