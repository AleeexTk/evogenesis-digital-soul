import tempfile
import unittest
from pathlib import Path

from packages.coordination.shared_task_manager import SharedTaskManager
from packages.execution.worker import ExecutionWorker
from packages.execution.termux.protocol import ExecutionResult


class _MockConnector:
    def execute(self, request):
        return ExecutionResult(ok=True, output=f"ok::{request.prompt}")


class ExecutionWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "shared_task.json"
        self.manager = SharedTaskManager(self.state)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pending_to_processing_to_done_with_event(self):
        task = self.manager.create_task("exec-test")
        worker = ExecutionWorker(self.manager, connector=_MockConnector())

        self.assertEqual(worker.run_once(), 1)

        updated = self.manager.list_tasks()[0]
        self.assertEqual(updated["id"], task["id"])
        self.assertEqual(updated["status"], "done")

        events = [item["event"] for item in updated["history"]]
        self.assertIn("agent.started", events)
        self.assertIn("task.completed", events)


if __name__ == "__main__":
    unittest.main()
