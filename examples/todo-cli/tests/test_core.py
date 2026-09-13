"""TC-04~TC-14：业务规则单元测试。"""

import tempfile
import unittest
from pathlib import Path

from todo.core import TodoApp
from todo.models import Priority, TodoError
from todo.storage import Storage


class TodoAppTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = TodoApp(Storage(path=Path(self.tmp.name) / "todos.json"))

    def tearDown(self):
        self.tmp.cleanup()


class TestAdd(TodoAppTestBase):
    def test_add_default_priority(self):
        todo = self.app.add("写周报")
        self.assertEqual(todo.id, 1)
        self.assertIs(todo.priority, Priority.NORMAL)
        self.assertFalse(todo.done)

    def test_add_custom_priority(self):
        todo = self.app.add("买咖啡", "high")
        self.assertIs(todo.priority, Priority.HIGH)

    def test_add_empty_content(self):
        with self.assertRaises(TodoError) as ctx:
            self.app.add("")
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_add_newline_rejected(self):
        """TC-C1：内容含换行符拒绝（fix-newline-content）"""
        with self.assertRaises(TodoError) as ctx:
            self.app.add("第一行\n第二行")
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_add_carriage_return_rejected(self):
        """TC-C2：内容含回车符拒绝（fix-newline-content）"""
        with self.assertRaises(TodoError) as ctx:
            self.app.add("带回车\r的内容")
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_add_invalid_priority(self):
        with self.assertRaises(TodoError) as ctx:
            self.app.add("x", "urgent")
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_add_persists_and_increments_id(self):
        self.app.add("a")
        second = self.app.add("b")
        self.assertEqual(second.id, 2)


class TestListSorted(TodoAppTestBase):
    def test_sorted_by_priority(self):
        self.app.add("低", "low")
        self.app.add("普通", "normal")
        self.app.add("高", "high")
        contents = [t.content for t in self.app.list_sorted()]
        self.assertEqual(contents, ["高", "普通", "低"])

    def test_same_priority_id_ascending(self):
        self.app.add("first")
        self.app.add("second")
        contents = [t.content for t in self.app.list_sorted()]
        self.assertEqual(contents, ["first", "second"])

    def test_done_after_undone(self):
        self.app.add("未完成", "low")
        self.app.add("已完成", "high")
        self.app.done(2)
        contents = [t.content for t in self.app.list_sorted()]
        self.assertEqual(contents, ["未完成", "已完成"])


class TestDone(TodoAppTestBase):
    def test_done_marks_and_persists(self):
        self.app.add("写周报")
        self.app.done(1)
        self.assertTrue(self.app.list_sorted()[0].done)

    def test_done_missing(self):
        with self.assertRaises(TodoError) as ctx:
            self.app.done(99)
        self.assertEqual(ctx.exception.exit_code, 1)

    def test_done_twice(self):
        self.app.add("写周报")
        self.app.done(1)
        with self.assertRaises(TodoError) as ctx:
            self.app.done(1)
        self.assertEqual(ctx.exception.exit_code, 1)


class TestRemove(TodoAppTestBase):
    def test_remove(self):
        self.app.add("写周报")
        removed = self.app.remove(1)
        self.assertEqual(removed.id, 1)
        self.assertEqual(self.app.list_sorted(), [])

    def test_remove_missing(self):
        with self.assertRaises(TodoError) as ctx:
            self.app.remove(99)
        self.assertEqual(ctx.exception.exit_code, 1)


class TestSetPriority(TodoAppTestBase):
    def test_set_priority(self):
        self.app.add("写周报")
        self.app.set_priority(1, "low")
        self.assertIs(self.app.list_sorted()[0].priority, Priority.LOW)

    def test_set_priority_invalid(self):
        self.app.add("写周报")
        with self.assertRaises(TodoError) as ctx:
            self.app.set_priority(1, "urgent")
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_set_priority_missing(self):
        with self.assertRaises(TodoError) as ctx:
            self.app.set_priority(99, "low")
        self.assertEqual(ctx.exception.exit_code, 1)


if __name__ == "__main__":
    unittest.main()
