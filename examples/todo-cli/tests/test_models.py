"""TC-01~TC-03：数据模型单元测试。"""

import unittest

from todo.models import Priority, Todo, TodoError


class TestPriority(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(Priority.HIGH.label, "高")
        self.assertEqual(Priority.NORMAL.label, "普通")
        self.assertEqual(Priority.LOW.label, "低")

    def test_from_str(self):
        self.assertIs(Priority.from_str("high"), Priority.HIGH)
        self.assertIs(Priority.from_str("normal"), Priority.NORMAL)
        self.assertIs(Priority.from_str("low"), Priority.LOW)

    def test_from_str_invalid(self):
        with self.assertRaises(ValueError):
            Priority.from_str("urgent")


class TestTodoSortKey(unittest.TestCase):
    def test_sort_key_ordering(self):
        low = Todo(id=1, content="low", priority=Priority.LOW)
        high = Todo(id=2, content="high", priority=Priority.HIGH)
        normal = Todo(id=3, content="normal", priority=Priority.NORMAL)
        self.assertLess(high.sort_key(), normal.sort_key())
        self.assertLess(normal.sort_key(), low.sort_key())

    def test_undone_before_done(self):
        done_high = Todo(id=1, content="done", priority=Priority.HIGH, done=True)
        undone_low = Todo(id=2, content="undone", priority=Priority.LOW)
        self.assertLess(undone_low.sort_key(), done_high.sort_key())

    def test_same_priority_id_ascending(self):
        a = Todo(id=1, content="a", priority=Priority.NORMAL)
        b = Todo(id=2, content="b", priority=Priority.NORMAL)
        self.assertLess(a.sort_key(), b.sort_key())


class TestTodoDict(unittest.TestCase):
    def test_roundtrip(self):
        todo = Todo(id=1, content="写周报", priority=Priority.HIGH, done=True)
        restored = Todo.from_dict(todo.to_dict())
        self.assertEqual(restored.id, 1)
        self.assertEqual(restored.content, "写周报")
        self.assertIs(restored.priority, Priority.HIGH)
        self.assertTrue(restored.done)

    def test_from_dict_broken(self):
        with self.assertRaises(TodoError):
            Todo.from_dict({"id": "x"})


if __name__ == "__main__":
    unittest.main()
