"""CLI utility for task lifecycle operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .shared_task_manager import SharedTaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared task manager CLI")
    parser.add_argument("--state", default="shared_task.json", help="Path to JSON state file")

    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a task")
    create.add_argument("prompt", help="Task prompt")

    sub.add_parser("show", help="Show all tasks")
    sub.add_parser("reset", help="Reset all tasks")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    manager = SharedTaskManager(Path(args.state))

    if args.command == "create":
        task = manager.create_task(args.prompt)
        print(json.dumps(task, ensure_ascii=False, indent=2))
    elif args.command == "show":
        print(json.dumps(manager.list_tasks(), ensure_ascii=False, indent=2))
    elif args.command == "reset":
        manager.reset()
        print("State reset.")


if __name__ == "__main__":
    main()
