from pathlib import Path

from packages.coordination.shared_task_manager import SharedTaskManager, TaskConflictError


def test_create_and_update_task(tmp_path: Path):
    state = tmp_path / "state.json"
    manager = SharedTaskManager(state)

    task = manager.create_task("hello")
    assert task["status"] == "pending"
    assert task["version"] == 1

    updated = manager.update_task(
        task["id"],
        expected_version=1,
        status="processed_by_ark",
        event="agent.started",
        agent_name="ark",
    )
    assert updated["status"] == "processed_by_ark"
    assert updated["version"] == 2


def test_optimistic_conflict(tmp_path: Path):
    manager = SharedTaskManager(tmp_path / "state.json")
    task = manager.create_task("hello")

    try:
        manager.update_task(task["id"], expected_version=0, status="failed")
        raised = False
    except TaskConflictError:
        raised = True

    assert raised
