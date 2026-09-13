"""业务规则层。对应 docs/02-design.md 第 3 节模块划分中的 core 模块。"""

from __future__ import annotations

from .models import Priority, Todo, TodoError
from .storage import Storage

EXIT_USAGE = 2  # 用法错误（参数不合法）
EXIT_BIZ = 1  # 业务错误（找不到待办等）


class TodoApp:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def add(self, content: str, priority: str | None = None) -> Todo:
        if not content.strip():
            raise TodoError("待办内容不能为空", EXIT_USAGE)
        if "\n" in content or "\r" in content:
            raise TodoError("待办内容不能包含换行符（会破坏列表逐行显示）", EXIT_USAGE)
        try:
            prio = Priority.from_str(priority) if priority else Priority.NORMAL
        except ValueError as exc:
            raise TodoError(str(exc), EXIT_USAGE) from exc
        todos = self.storage.load()
        new_id = max((t.id for t in todos), default=0) + 1
        todo = Todo(id=new_id, content=content, priority=prio)
        todos.append(todo)
        self.storage.save(todos)
        return todo

    def list_sorted(self) -> list[Todo]:
        return sorted(self.storage.load(), key=lambda t: t.sort_key())

    def _find(self, todos: list[Todo], todo_id: int) -> Todo:
        for todo in todos:
            if todo.id == todo_id:
                return todo
        raise TodoError(f"待办 #{todo_id} 不存在", EXIT_BIZ)

    def done(self, todo_id: int) -> Todo:
        todos = self.storage.load()
        todo = self._find(todos, todo_id)
        if todo.done:
            raise TodoError(f"待办 #{todo_id} 已经完成，无需重复操作", EXIT_BIZ)
        todo.done = True
        self.storage.save(todos)
        return todo

    def remove(self, todo_id: int) -> Todo:
        todos = self.storage.load()
        todo = self._find(todos, todo_id)
        todos.remove(todo)
        self.storage.save(todos)
        return todo

    def set_priority(self, todo_id: int, priority: str) -> Todo:
        try:
            prio = Priority.from_str(priority)
        except ValueError as exc:
            raise TodoError(str(exc), EXIT_USAGE) from exc
        todos = self.storage.load()
        todo = self._find(todos, todo_id)
        todo.priority = prio
        self.storage.save(todos)
        return todo
