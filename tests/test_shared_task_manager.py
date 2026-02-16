import tempfile
import unittest
from pathlib import Path

from packages.coordination.shared_task_manager import (
    InvalidTaskTransitionError,
    SharedTaskManager,
    TaskConflictError,
    TaskUpdate,
)
from packages.coordination.watcher_ark import ArkWatcher
from packages.coordination.watcher_omega import OmegaWatcher


class SharedTaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "shared_task.json"
        self.manager = SharedTaskManager(self.state)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_progress_task_with_events(self):
        task = self.manager.create_task("hello")
        self.assertEqual(task["status"], "pending")
        self.assertEqual(task["history"][0]["event"], "task.created")

        started = self.manager.update_task(
            TaskUpdate(
                task_id=task["id"],
                status="processing_by_ark",
                agent="ark",
                expected_version=0,
            )
        )
        self.assertEqual(started["history"][-1]["event"], "agent.started")

        responded = self.manager.update_task(
            TaskUpdate(
                task_id=task["id"],
                status="processed_by_ark",
                agent="ark",
                expected_version=1,
                response="ark:ok",
            )
        )
        self.assertEqual(responded["history"][-1]["event"], "agent.response")

        omega_started = self.manager.update_task(
            TaskUpdate(
                task_id=task["id"],
                status="processing_by_omega",
                agent="omega",
                expected_version=2,
            )
        )
        done = self.manager.update_task(
            TaskUpdate(
                task_id=task["id"],
                status="complete",
                agent="omega",
                expected_version=omega_started["version"],
            )
        )
        self.assertEqual(done["history"][-1]["event"], "task.completed")

    def test_version_conflict_raises(self):
        task = self.manager.create_task("conflict")
        with self.assertRaises(TaskConflictError):
            self.manager.update_task(
                TaskUpdate(
                    task_id=task["id"],
                    status="processing_by_ark",
                    agent="ark",
                    expected_version=99,
                )
            )

    def test_invalid_transition_raises(self):
        task = self.manager.create_task("invalid")
        with self.assertRaises(InvalidTaskTransitionError):
            self.manager.update_task(
                TaskUpdate(
                    task_id=task["id"],
                    status="complete",
                    agent="omega",
                    expected_version=0,
                )
            )

    def test_watchers_pipeline(self):
        self.manager.create_task("watch")
        ark = ArkWatcher(self.manager, process_fn=lambda p: f"ark::{p}")
        omega = OmegaWatcher(self.manager, process_fn=lambda p: f"omega::{p}")

        self.assertEqual(ark.run_once(), 1)
        self.assertEqual(omega.run_once(), 1)

        tasks = self.manager.list_tasks()
        self.assertEqual(tasks[0]["status"], "complete")

    def test_watcher_failure_marks_task_failed(self):
        self.manager.create_task("boom")

        def _raise(_: str) -> str:
            raise RuntimeError("ark exploded")

        ark = ArkWatcher(self.manager, process_fn=_raise)
        self.assertEqual(ark.run_once(), 0)

        task = self.manager.list_tasks()[0]
        self.assertEqual(task["status"], "failed")
        self.assertEqual(task["history"][-1]["event"], "task.failed")


if __name__ == "__main__":
    unittest.main()
