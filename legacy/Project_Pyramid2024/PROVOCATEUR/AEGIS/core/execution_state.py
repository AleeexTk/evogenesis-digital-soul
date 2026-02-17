from __future__ import annotations
from enum import Enum
from typing import Dict, Set, Optional, List
from datetime import datetime

class ExecutionState(str, Enum):
    """
    Deterministic System States.
    Defines the mathematical boundaries of system behavior.
    """
    BOOTING = "BOOTING"
    IDLE = "IDLE"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    FROZEN = "FROZEN"
    ERROR = "ERROR"

# Valid transitions: State -> {Allowed Next States}
ALLOWED_TRANSITIONS: Dict[ExecutionState, Set[ExecutionState]] = {
    ExecutionState.BOOTING: {ExecutionState.IDLE, ExecutionState.ERROR},
    ExecutionState.IDLE: {ExecutionState.ANALYZING, ExecutionState.FROZEN, ExecutionState.ERROR},
    ExecutionState.ANALYZING: {ExecutionState.PLANNING, ExecutionState.IDLE, ExecutionState.ERROR},
    ExecutionState.PLANNING: {ExecutionState.EXECUTING, ExecutionState.IDLE, ExecutionState.ERROR},
    ExecutionState.EXECUTING: {ExecutionState.VERIFYING, ExecutionState.ERROR},
    ExecutionState.VERIFYING: {ExecutionState.IDLE, ExecutionState.ERROR},
    ExecutionState.FROZEN: {ExecutionState.IDLE, ExecutionState.BOOTING},
    ExecutionState.ERROR: {ExecutionState.BOOTING, ExecutionState.IDLE}
}

class StateManager:
    """
    Atomic State Controller to ensure system determinism.
    """
    def __init__(self, initial_state: ExecutionState = ExecutionState.BOOTING):
        self._current_state = initial_state
        self._history: List[Dict[str, str]] = []
        self._record_transition(None, initial_state, "System initialized")

    @property
    def current_state(self) -> ExecutionState:
        return self._current_state

    def transition_to(self, target: ExecutionState, reason: str = "Unspecified") -> bool:
        """
        Attempt to transition to a new state.
        Returns True if successful, False if illegal.
        """
        if target == self._current_state:
            return True

        allowed = ALLOWED_TRANSITIONS.get(self._current_state, set())
        
        # Security Override: ERROR and FROZEN can be reached from anywhere in emergencies
        if target in (ExecutionState.ERROR, ExecutionState.FROZEN) or target in allowed:
            old_state = self._current_state
            self._current_state = target
            self._record_transition(old_state, target, reason)
            return True
        
        print(f"[AEGIS] ILLEGAL TRANSITION BLOCKED: {self._current_state} -> {target}")
        return False

    def _record_transition(self, from_state: Optional[ExecutionState], to_state: ExecutionState, reason: str):
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "from": from_state.value if from_state else "START",
            "to": to_state.value,
            "reason": reason
        })
        # Keep history manageable
        if len(self._history) > 100:
            self._history.pop(0)

    def get_history(self) -> List[Dict[str, str]]:
        return self._history

state_manager = StateManager()
