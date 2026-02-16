import tempfile
import unittest
from pathlib import Path

from packages.coordination.shared_task_manager import (
    SharedTaskManager,
    TaskConflictError,
    TaskUpdate,
)


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


if __name__ == "__main__":
    unittest.main()
