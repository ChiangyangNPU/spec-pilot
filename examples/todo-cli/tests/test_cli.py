"""TC-18~TC-30：CLI 端到端测试（subprocess 真实进程执行，客观裁判规则）。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "todo.py"


def run_cli(args, env_file):
    env = os.environ.copy()
    env["TODO_FILE"] = str(env_file)
    return subprocess.run(
        [sys.executable, str(LAUNCHER), *args],
        capture_output=True, text=True, env=env, timeout=10,
    )


class CliTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.todo_file = Path(self.tmp.name) / "todos.json"

    def tearDown(self):
        self.tmp.cleanup()


class TestAddCommand(CliTestBase):
    def test_add_high(self):
        result = run_cli(["add", "写周报", "-p", "high"], self.todo_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("#1 [高] 写周报", result.stdout)

    def test_add_empty_content(self):
        result = run_cli(["add", ""], self.todo_file)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr)

    def test_add_invalid_priority(self):
        result = run_cli(["add", "x", "-p", "urgent"], self.todo_file)
        self.assertEqual(result.returncode, 2)

    def test_add_multiline_rejected(self):
        """TC-C1：多行内容退出码 2，不写入数据（fix-newline-content）"""
        result = run_cli(["add", "第一行\n第二行"], self.todo_file)
        self.assertEqual(result.returncode, 2)
        self.assertIn("换行", result.stderr)
        self.assertFalse(self.todo_file.exists())

    def test_add_cr_rejected(self):
        """TC-C2：含 \r 的内容退出码 2（fix-newline-content）"""
        result = run_cli(["add", "带回车\r的内容"], self.todo_file)
        self.assertEqual(result.returncode, 2)
        self.assertIn("换行", result.stderr)

    def test_legacy_multiline_file_still_loads(self):
        """TC-C4：修复前保存的多行历史数据 load/list 不崩溃（fix-newline-content）"""
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        self.todo_file.write_text(
            json.dumps([{"id": 1, "content": "旧数据\n第二行", "priority": "normal", "done": False}],
                       ensure_ascii=False),
            encoding="utf-8",
        )
        result = run_cli(["list"], self.todo_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("旧数据", result.stdout)


class TestListCommand(CliTestBase):
    def test_list_sorted_by_priority(self):
        for content, prio in [("低任务", "low"), ("普通任务", "normal"), ("高任务", "high")]:
            run_cli(["add", content, "-p", prio], self.todo_file)
        result = run_cli(["list"], self.todo_file)
        self.assertEqual(result.returncode, 0)
        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 3)
        self.assertIn("高任务", lines[0])
        self.assertIn("普通任务", lines[1])
        self.assertIn("低任务", lines[2])

    def test_list_empty(self):
        result = run_cli(["list"], self.todo_file)
        self.assertEqual(result.returncode, 0)
        self.assertIn("暂无待办", result.stdout)


class TestDoneCommand(CliTestBase):
    def test_done_marks_in_list(self):
        run_cli(["add", "任务A"], self.todo_file)
        run_cli(["add", "任务B"], self.todo_file)
        result = run_cli(["done", "1"], self.todo_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = run_cli(["list"], self.todo_file).stdout.splitlines()
        done_line = next(ln for ln in listing if "[x]" in ln)
        self.assertIn("任务A", done_line)
        self.assertEqual(listing.index(done_line), 1)  # 排在未完成之后

    def test_done_missing(self):
        result = run_cli(["done", "99"], self.todo_file)
        self.assertEqual(result.returncode, 1)
        self.assertIn("不存在", result.stderr)

    def test_done_twice(self):
        run_cli(["add", "任务A"], self.todo_file)
        run_cli(["done", "1"], self.todo_file)
        result = run_cli(["done", "1"], self.todo_file)
        self.assertEqual(result.returncode, 1)


class TestRemoveCommand(CliTestBase):
    def test_rm(self):
        run_cli(["add", "任务A"], self.todo_file)
        result = run_cli(["rm", "1"], self.todo_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("暂无待办", run_cli(["list"], self.todo_file).stdout)

    def test_rm_missing(self):
        result = run_cli(["rm", "99"], self.todo_file)
        self.assertEqual(result.returncode, 1)


class TestPriCommand(CliTestBase):
    def test_pri_to_low(self):
        run_cli(["add", "任务A"], self.todo_file)
        result = run_cli(["pri", "1", "low"], self.todo_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[低]", run_cli(["list"], self.todo_file).stdout)

    def test_pri_missing(self):
        result = run_cli(["pri", "99", "high"], self.todo_file)
        self.assertEqual(result.returncode, 1)

    def test_pri_invalid_priority(self):
        run_cli(["add", "任务A"], self.todo_file)
        result = run_cli(["pri", "1", "urgent"], self.todo_file)
        self.assertEqual(result.returncode, 2)


class TestPersistence(CliTestBase):
    def test_todo_file_env_writes_json(self):
        result = run_cli(["add", "a"], self.todo_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.todo_file.exists())
        raw = json.loads(self.todo_file.read_text(encoding="utf-8"))
        self.assertIsInstance(raw, list)
        self.assertEqual(raw[0]["content"], "a")


if __name__ == "__main__":
    unittest.main()
