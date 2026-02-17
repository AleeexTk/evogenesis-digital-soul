from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import os

class DecisionAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    DELAY = "delay"
    FALLBACK = "fallback"

@dataclass(frozen=True)
class PolicyDecision:
    action: DecisionAction
    reason: str
    policy_rules: List[str]
    modified_params: Optional[Dict[str, Any]] = None
    delay_seconds: Optional[float] = None

def _to_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None

def _match_condition(condition: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    """
    Проверка условия. Поддерживает операторы: lt, lte, gt, gte, ne, in, not_in.
    """
    for key, expected in condition.items():
        actual = ctx.get(key)

        # 1. Простая проверка равенства
        if not isinstance(expected, dict):
            if actual != expected:
                return False
            continue

        # 2. Операторы
        for op, val in expected.items():
            if op in ("lt", "lte", "gt", "gte"):
                a = _to_float(actual)
                b = _to_float(val)
                if a is None or b is None:
                    return False
                if op == "lt" and not (a < b): return False
                if op == "lte" and not (a <= b): return False
                if op == "gt" and not (a > b): return False
                if op == "gte" and not (a >= b): return False
            elif op == "ne":
                if actual == val: return False
            elif op == "in":
                if actual not in list(val): return False
            elif op == "not_in":
                if actual in list(val): return False
            else:
                return False
    return True

class PolicyEngine:
    """
    AEGIS Policy Engine: Детерминированный движок правил.
    Принимает контекст -> Возвращает решение (ALLOW/DENY/DELAY).
    """
    def __init__(self, rules: Optional[Dict[str, Any]] = None, config_path: str = "security_policies.yaml"):
        if rules is not None:
            self.rules = rules
            return

        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.rules = yaml.safe_load(f) or {}
            else:
                print(f"[AEGIS] Warning: Policy file {config_path} not found. Using default empty rules.")
                self.rules = {}
        except ImportError:
            print("[AEGIS] PyYAML not installed. Policies will be empty.")
            self.rules = {}

    def evaluate(self, ctx: Dict[str, Any]) -> PolicyDecision:
        # 1. DENY
        for i, rule in enumerate(self.rules.get("deny", [])):
            if _match_condition(rule.get("condition", {}), ctx):
                return PolicyDecision(
                    action=DecisionAction.DENY,
                    reason=rule.get("reason", "blocked by AEGIS"),
                    policy_rules=[f"deny[{i}]"],
                )

        # 2. DELAY
        for i, rule in enumerate(self.rules.get("delay", [])):
            if _match_condition(rule.get("condition", {}), ctx):
                return PolicyDecision(
                    action=DecisionAction.DELAY,
                    reason=rule.get("reason", "delayed by AEGIS"),
                    policy_rules=[f"delay[{i}]"],
                    delay_seconds=float(rule.get("delay_seconds", 0.5)),
                )

        # 3. FALLBACK
        for i, rule in enumerate(self.rules.get("fallback", [])):
            if _match_condition(rule.get("condition", {}), ctx):
                modified = rule.get("modified_params") or {}
                return PolicyDecision(
                    action=DecisionAction.FALLBACK,
                    reason=rule.get("reason", "fallback by AEGIS"),
                    policy_rules=[f"fallback[{i}]"],
                    modified_params=modified,
                )

        # DEFAULT ALLOW
        return PolicyDecision(
            action=DecisionAction.ALLOW,
            reason="default allow",
            policy_rules=["default"],
        )
