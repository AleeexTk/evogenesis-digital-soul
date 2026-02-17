import sys
import os
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PROVOCATEUR.AEGIS.core.execution_state import ExecutionState, state_manager

class CoreOrchestrator:
    """
    Electronic Brain for the Pyramid.
    Acts as the central coordination unit for all modules.
    Now enforced by AEGIS Atomic State.
    """
    def __init__(self):
        self.active_module = "CORE"
        self.last_tick = datetime.now()
        self.task_queue = []
        self.current_task = None
        self.metrics = {
            "cycle_count": 0,
            "uptime_seconds": 0,
            "anomaly_score": 0.0
        }
        self.running = True
        
        # Initialize state to IDLE via manager
        state_manager.transition_to(ExecutionState.IDLE, "System boot complete")
        
        # Start the heartbeat thread
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    @property
    def state(self) -> ExecutionState:
        return state_manager.current_state

    def _run_loop(self):
        """Main cognitive cycle loop."""
        print("[CORE] Orchestrator loop started.")
        start_time = time.time()
        
        while self.running:
            self.metrics["uptime_seconds"] = int(time.time() - start_time)
            self._process_tick()
            time.sleep(1) # 1Hz heartbeat

    def _process_tick(self):
        """
        Deterministic processing of system cycles.
        Transitions are now purely event-driven or logic-driven, not random.
        """
        # Module logic depends on current state
        if self.state == ExecutionState.IDLE:
            if self.task_queue:
                self.current_task = self.task_queue.pop(0)
                self.transition_to(ExecutionState.ANALYZING, f"Task Received: {self.current_task}")
        
        # Placeholder for real logic - in production these would call module APIs
        pass

    def transition_to(self, target: ExecutionState, reason: str = "Unspecified"):
        """
        Explicit state change enforced by AEGIS.
        """
        if state_manager.transition_to(target, reason):
            # Update active module based on state mapping
            mapping = {
                ExecutionState.ANALYZING: "PURPLE_TRIANGLE",
                ExecutionState.PLANNING: "TRAILBLAZER",
                ExecutionState.EXECUTING: "TRAILBLAZER",
                ExecutionState.VERIFYING: "SOUL",
                ExecutionState.ERROR: "PROVOCATEUR",
                ExecutionState.FROZEN: "PROVOCATEUR"
            }
            self.active_module = mapping.get(target, "CORE")
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Return full system snapshot with formal state and history."""
        return {
            "state": self.state,
            "active_module": self.active_module,
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "current_task": self.current_task,
            "state_history": state_manager.get_history()[-5:] # Last 5 transitions
        }

    def execute_command(self, cmd: str):
        """External trigger for formal state transitions."""
        cmd = cmd.upper()
        if cmd == "START_ANALYSIS":
            self.transition_to(ExecutionState.ANALYZING, "External command")
        elif cmd == "START_PLAN":
            self.transition_to(ExecutionState.PLANNING, "External command")
        elif cmd == "START_EXECUTION":
            self.transition_to(ExecutionState.EXECUTING, "External command")
        elif cmd == "RESET":
            self.transition_to(ExecutionState.IDLE, "Manual reset")
        elif cmd == "TRIGGER_ERROR":
            self.transition_to(ExecutionState.ERROR, "Simulated failure")

# Singleton instance
core = CoreOrchestrator()
