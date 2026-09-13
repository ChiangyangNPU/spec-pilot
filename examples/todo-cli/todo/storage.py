"""JSON 文件持久化。对应 docs/02-design.md 第 6 节数据库设计。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Todo, TodoError

DEFAULT_FILE = Path.home() / ".todo-cli.json"


class Storage:
    def __init__(self, path: Path | None = None) -> None:
        env_path = os.environ.get("TODO_FILE")
        self.path = Path(path) if path else Path(env_path) if env_path else DEFAULT_FILE

    def load(self) -> list[Todo]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise TodoError(f"待办文件格式错误：{self.path}", 1)
            return [Todo.from_dict(item) for item in raw]
        except json.JSONDecodeError as exc:
            # 损坏文件必须报错而不是清空用户数据（FR-6 / TC-17）
            raise TodoError(f"待办文件损坏，无法读取：{self.path}（{exc}）", 1) from exc

    def save(self, todos: list[Todo]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps([t.to_dict() for t in todos], ensure_ascii=False, indent=2)
        # 原子写：先写临时文件再 rename，进程中断不会留下半截 JSON
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.write(data)
            os.replace(tmp_name, self.path)
        except OSError:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
