"""薄编排器自身的单元测试：熔断状态机与 Markdown 解析。

运行：python3 orchestrator/tests/test_specpilot.py
（或 python3 -m unittest discover -s orchestrator/tests）
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from specpilot import (  # noqa: E402
    MAX_ROUNDS,
    apply_test_result,
    coverage_gaps,
    extract_section,
    requirement_ids,
    srs_requirement_problems,
)


class TestApplyTestResult(unittest.TestCase):
    def test_success_resets_rounds(self):
        state = {"rounds": 3, "tripped": False, "history": []}
        new, entry = apply_test_result(state, 0, "pytest")
        self.assertEqual(new["rounds"], 0)
        self.assertFalse(new["tripped"])
        self.assertEqual(entry["exit_code"], 0)

    def test_fail_increments(self):
        state = {"rounds": 0, "tripped": False, "history": []}
        new, _ = apply_test_result(state, 1, "pytest")
        self.assertEqual(new["rounds"], 1)
        self.assertFalse(new["tripped"])

    def test_breaker_trips_at_max(self):
        state = {"rounds": 0, "tripped": False, "history": []}
        for i in range(MAX_ROUNDS - 1):
            state, _ = apply_test_result(state, 1, "pytest")
            self.assertFalse(state["tripped"], f"第 {i + 1} 轮不应熔断")
        state, entry = apply_test_result(state, 1, "pytest")
        self.assertTrue(state["tripped"])
        self.assertTrue(entry.get("tripped"))
        self.assertEqual(state["rounds"], MAX_ROUNDS)

    def test_history_capped(self):
        state = {"rounds": 0, "tripped": False, "history": []}
        for _ in range(60):
            state, _ = apply_test_result(state, 0, "pytest")
        self.assertLessEqual(len(state["history"]), 50)

    def test_source_recorded(self):
        state = {"rounds": 0, "tripped": False, "history": []}
        _, entry_ci = apply_test_result(state, 0, "pytest", source="ci")
        self.assertEqual(entry_ci["source"], "ci")
        _, entry_session = apply_test_result(state, 0, "pytest")
        self.assertEqual(entry_session["source"], "session")


class TestSrsParsing(unittest.TestCase):
    def test_missing_acceptance_detected(self):
        srs = """| 编号 | 需求描述 | 关联用例 | 优先级 | 验收标准（可自动验证） |
|------|----------|----------|--------|------------------------|
| FR-1 | 添加待办 | UC-1 | 必须 | |
| FR-2 | 删除待办 | UC-2 | 必须 | `rm <id>` 后列表不含该 ID |
| NFR-1 | 性能 | | | |
"""
        problems = srs_requirement_problems(srs)
        self.assertEqual(len(problems), 2)
        self.assertIn("FR-1", problems[0])
        self.assertIn("NFR-1", problems[1])

    def test_complete_table_passes(self):
        srs = """| 编号 | 需求描述 | 关联用例 | 优先级 | 验收标准 |
|------|----------|----------|--------|----------|
| FR-1 | 添加待办 | UC-1 | 必须 | 退出码 0 |
| NFR-1 | 性能 | | | time ≤ 0.5s |
"""
        self.assertEqual(srs_requirement_problems(srs), [])

    def test_requirement_ids(self):
        srs = "| FR-1 | x |\n| FR-1 | x |\n| NFR-2 | y |\n| 其他 | z |"
        self.assertEqual(requirement_ids(srs), ["FR-1", "NFR-2"])


class TestCoverageGaps(unittest.TestCase):
    def test_gap_detected(self):
        tc = """## 2. 需求覆盖矩阵

| 需求编号 | 对应用例 ID | 覆盖情况 |
|----------|-------------|----------|
| FR-1 | TC-01 | ✅ 已覆盖 |
| FR-2 | — | ❌ 缺口 |

## 3. 其他
"""
        gaps, found = coverage_gaps(tc)
        self.assertTrue(found)
        self.assertEqual(len(gaps), 1)
        self.assertIn("FR-2", gaps[0])

    def test_section_missing(self):
        gaps, found = coverage_gaps("没有任何矩阵的文档")
        self.assertFalse(found)
        self.assertEqual(gaps, [])

    def test_extract_section(self):
        text = "## A\n内容1\n## 覆盖矩阵\n矩阵行\n## C\n其他"
        self.assertEqual(extract_section(text, "覆盖矩阵"), "矩阵行")


if __name__ == "__main__":
    unittest.main()
