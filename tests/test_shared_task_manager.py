import tempfile
import unittest
from pathlib import Path

from packages.coordination.shared_task_manager import (
    SharedTaskManager,
    TaskConflictError,
    TaskUpdate,
)
from packages.stream.websocket_bridge import normalize_task_events


class SharedTaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "shared_task.json"
        self.manager = SharedTaskManager(self.state)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_progress_task(self):
        task = self.manager.create_task("hello")
        self.assertEqual(task["status"], "pending")

        after_ark = self.manager.update_task(
            TaskUpdate(
                task_id=task["id"],
                status="processed_by_ark",
                agent="ark",
                expected_version=0,
            )
        )
        self.assertEqual(after_ark["status"], "processed_by_ark")

        after_omega = self.manager.update_task(
            TaskUpdate(
                task_id=task["id"],
                status="complete",
                agent="omega",
                expected_version=1,
            )
        )
        self.assertEqual(after_omega["status"], "complete")

    def test_version_conflict_raises(self):
        task = self.manager.create_task("conflict")
        with self.assertRaises(TaskConflictError):
            self.manager.update_task(
                TaskUpdate(
                    task_id=task["id"],
                    status="processed_by_ark",
                    agent="ark",
                    expected_version=99,
                )
            )


class WebsocketBridgeNormalizationTests(unittest.TestCase):
    def test_normalize_uses_event_local_status_and_version(self):
        task = {
            "id": "t-1",
            "status": "complete",
            "version": 2,
            "history": [
                {"event": "task.created", "at": 1.0, "metadata": {"source": "cli"}},
                {
                    "event": "agent.started",
                    "at": 2.0,
                    "agent": "ark",
                    "status": "processed_by_ark",
                    "version": 1,
                },
                {
                    "event": "agent.response",
                    "at": 3.0,
                    "agent": "omega",
                    "status": "complete",
                    "version": 2,
                    "response": "done",
                },
            ],
        }

        frames = normalize_task_events(task)

        self.assertEqual(frames[0]["type"], "task.created")
        self.assertEqual(frames[0]["payload"]["status"], "pending")
        self.assertEqual(frames[0]["payload"]["version"], 0)

        self.assertEqual(frames[1]["type"], "agent.started")
        self.assertEqual(frames[1]["payload"]["status"], "processed_by_ark")
        self.assertEqual(frames[1]["payload"]["version"], 1)

        self.assertEqual(frames[2]["type"], "agent.response")
        self.assertEqual(frames[2]["payload"]["status"], "complete")
        self.assertEqual(frames[2]["payload"]["version"], 2)


if __name__ == "__main__":
    unittest.main()
