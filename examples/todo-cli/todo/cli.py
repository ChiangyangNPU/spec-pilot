"""命令行入口。对应 docs/02-design.md 第 9 节接口定义（子命令表）。"""

from __future__ import annotations

import argparse
import sys

from .core import TodoApp
from .models import Todo, TodoError
from .storage import Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="命令行待办事项工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加待办")
    p_add.add_argument("content", help="待办内容")
    p_add.add_argument("-p", "--priority", default=None, help="优先级：high/normal/low")

    sub.add_parser("list", help="查看待办列表")

    p_done = sub.add_parser("done", help="完成待办")
    p_done.add_argument("id", type=int, help="待办 ID")

    p_rm = sub.add_parser("rm", help="删除待办")
    p_rm.add_argument("id", type=int, help="待办 ID")

    p_pri = sub.add_parser("pri", help="修改优先级")
    p_pri.add_argument("id", type=int, help="待办 ID")
    p_pri.add_argument("priority", help="优先级：high/normal/low")

    return parser


def render(todo: Todo) -> str:
    mark = "[x] " if todo.done else ""
    return f"{mark}#{todo.id} [{todo.priority.label}] {todo.content}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = TodoApp(Storage())
    try:
        if args.command == "add":
            todo = app.add(args.content, args.priority)
            print(f"已添加：#{todo.id} [{todo.priority.label}] {todo.content}")
        elif args.command == "list":
            todos = app.list_sorted()
            if not todos:
                print("暂无待办")
            else:
                for todo in todos:
                    print(render(todo))
        elif args.command == "done":
            todo = app.done(args.id)
            print(f"已完成：#{todo.id}")
        elif args.command == "rm":
            todo = app.remove(args.id)
            print(f"已删除：#{todo.id}")
        elif args.command == "pri":
            todo = app.set_priority(args.id, args.priority)
            print(f"已修改优先级：#{todo.id} → {todo.priority.label}")
    except TodoError as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
