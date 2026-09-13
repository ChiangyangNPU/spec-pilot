"""数据模型：Todo、优先级枚举与业务异常。

对应 docs/02-design.md 第 4 节核心类图，模块间依赖的最底层。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    """三档优先级。_WEIGHT 越小越靠前，供 sort_key 使用。"""

    HIGH = ("high", "高", 0)
    NORMAL = ("normal", "普通", 1)
    LOW = ("low", "低", 2)

    def __init__(self, key: str, label: str, weight: int) -> None:
        self.key = key
        self._label = label
        self._weight = weight

    @property
    def label(self) -> str:
        return self._label

    @property
    def weight(self) -> int:
        return self._weight

    @classmethod
    def from_str(cls, value: str) -> "Priority":
        for member in cls:
            if member.key == value:
                return member
        raise ValueError(f"非法优先级：{value}（可选 high/normal/low）")


@dataclass
class TodoError(Exception):
    """业务错误。exit_code: 0 成功 / 1 业务错误 / 2 用法错误。"""

    message: str
    exit_code: int = 1


@dataclass
class Todo:
    id: int
    content: str
    priority: Priority = Priority.NORMAL
    done: bool = False

    def sort_key(self) -> tuple[int, int, int]:
        """列表排序键：未完成在前、优先级权重升序、同级 ID 升序。"""
        return (1 if self.done else 0, self.priority.weight, self.id)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "priority": self.priority.key,
            "done": self.done,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Todo":
        try:
            return cls(
                id=int(data["id"]),
                content=data["content"],
                priority=Priority.from_str(data["priority"]),
                done=bool(data["done"]),
            )
        except (KeyError, ValueError) as exc:
            raise TodoError(f"待办数据损坏：{data!r}（{exc}）", 1) from exc
