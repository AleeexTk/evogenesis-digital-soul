"""
PROVOCATEUR/AEGIS/core/deduplication_engine.py

Signature-based loop detection and deduplication.
Detects repetitive patterns in agent actions.
"""

import hashlib
import json
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple


class DeduplicationEngine:
    """
    Stateful engine to detect repeated actions and infinite loops.
    Uses a sliding window of recent fingerprints.
    """

    def __init__(self, window_size: int = 50, ttl_seconds: int = 300):
        self.window_size = window_size
        self.ttl_seconds = ttl_seconds
        # List of (timestamp, fingerprint)
        self.history: deque[Tuple[float, str]] = deque(maxlen=window_size)

    def _generate_fingerprint(self, ctx: Dict[str, Any]) -> str:
        """
        Creates a deterministic hash of the action context.
        Focuses on origin, intent, provider and params.
        """
        # Select relevant fields for deduplication
        id_fields = {
            "origin": ctx.get("origin"),
            "intent": ctx.get("intent"),
            "provider": ctx.get("provider"),
            "method": ctx.get("method"),
            "url": ctx.get("url"),
            "tool": ctx.get("tool"),
            # Recursively sort dicts for stable hash
            "params": json.dumps(ctx.get("params") or ctx.get("meta") or {}, sort_keys=True)
        }
        
        raw_str = json.dumps(id_fields, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def check_and_record(self, ctx: Dict[str, Any]) -> int:
        """
        Records the current action and returns the count of identical recent actions.
        """
        now = time.time()
        fp = self._generate_fingerprint(ctx)
        
        # Cleanup old entries (outside TTL)
        while self.history and (now - self.history[0][0]) > self.ttl_seconds:
            self.history.popleft()
            
        # Count occurrences in window
        count = sum(1 for ts, existing_fp in self.history if existing_fp == fp)
        
        # Record this one
        self.history.append((now, fp))
        
        return count + 1 # +1 because we include the current one 
