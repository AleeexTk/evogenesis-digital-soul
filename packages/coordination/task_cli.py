"""CLI manager for shared task state (create/show/reset)."""

from __future__ import annotations

import argparse
import json

from .shared_task_manager import SharedTaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared task board CLI")
    parser.add_argument("--state-file", default="shared_task.json")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a pending task")
    create.add_argument("prompt")

    show = sub.add_parser("show", help="Show tasks")
    show.add_argument("--status", default=None)

    sub.add_parser("reset", help="Reset state file")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manager = SharedTaskManager(args.state_file)

    if args.command == "create":
        print(json.dumps(manager.create_task(args.prompt), indent=2, ensure_ascii=False))
    elif args.command == "show":
        print(json.dumps(manager.list_tasks(status=args.status), indent=2, ensure_ascii=False))
    elif args.command == "reset":
        manager.reset()
        print('{"ok": true}')


if __name__ == "__main__":
    main()
