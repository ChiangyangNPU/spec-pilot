"""TC-15~TC-17：持久化单元测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from todo.models import Todo, TodoError
from todo.storage import Storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "todos.json"
        self.storage = Storage(path=self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_missing_file_returns_empty(self):
        self.assertEqual(self.storage.load(), [])

    def test_roundtrip(self):
        todos = [
            Todo(id=1, content="写周报"),
            Todo(id=2, content="买咖啡", done=True),
        ]
        self.storage.save(todos)
        restored = self.storage.load()
        self.assertEqual([t.to_dict() for t in restored], [t.to_dict() for t in todos])

    def test_broken_json_raises(self):
        self.path.write_text('{"broken":', encoding="utf-8")
        with self.assertRaises(TodoError):
            self.storage.load()
        # 损坏文件未被清空（TC-17：不清空用户数据）
        self.assertIn("broken", self.path.read_text(encoding="utf-8"))

    def test_save_is_valid_json_array(self):
        self.storage.save([Todo(id=1, content="a")])
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertIsInstance(raw, list)


if __name__ == "__main__":
    unittest.main()
