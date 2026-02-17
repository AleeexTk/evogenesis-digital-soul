"""Run execution worker."""

from packages.coordination.shared_task_manager import SharedTaskManager
from packages.execution.worker import ExecutionWorker


if __name__ == "__main__":
    ExecutionWorker(SharedTaskManager()).run_forever()
