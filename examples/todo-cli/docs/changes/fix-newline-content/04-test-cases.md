# 变更测试用例（冻结）—— fix-newline-content

> 依据本变更 spec.md 生成（编码开始前冻结，未参考实现）。用例编号加 `C` 前缀与主运行 TC-01~30 区分。

| 用例 ID | 来源验收标准 | 前置条件 | 步骤 | 输入 | 预期结果 |
|---------|--------------|----------|------|------|----------|
| TC-C1 | A-1 | `TODO_FILE` 指向临时空文件 | 子进程执行添加 | `todo add "第一行\n第二行"` | 退出码 2；stderr 含"换行"；数据文件无新条目 |
| TC-C2 | A-2 | 同上 | 子进程执行添加 | `todo add "带回车\r的内容"` | 退出码 2；stderr 含"换行" |
| TC-C3 | A-3 | 正常单行内容 | 全量回归主运行用例 | —— | 既有 42 个单元测试全部通过 |
| TC-C4 | A-4 | 数据文件为修复前合法保存的多行待办（手工构造 JSON） | 子进程查看列表 | `todo list` | 退出码 0；不崩溃（多行条目渲染保持原样） |

单元测试方法名/文档串携带来源用例 ID（追溯约定见 SKILL 阶段 3）：
- `test_core.TestAdd.test_add_newline_rejected`（TC-C1 单元层）
- `test_core.TestAdd.test_add_carriage_return_rejected`（TC-C2 单元层）
- `test_cli.TestAddCommand.test_add_multiline_rejected`（TC-C1 端到端）
- `test_cli.TestAddCommand.test_add_cr_rejected`（TC-C2 端到端）
- `test_cli.TestAddCommand.test_legacy_multiline_file_still_loads`（TC-C4 端到端）
- TC-C3 由既有 TC-18/TC-21 测试承担回归

## 2. 覆盖矩阵

| 验收标准 | 对应用例 | 覆盖情况 |
|----------|----------|----------|
| A-1 | TC-C1（端到端 + 单元层） | ✅ 已覆盖 |
| A-2 | TC-C2（端到端 + 单元层） | ✅ 已覆盖 |
| A-3 | TC-C3（既有 TC-18/TC-21 回归） | ✅ 已覆盖 |
| A-4 | TC-C4 | ✅ 已覆盖 |

## 3. 用例变更记录

| 日期 | 用例 | 变更 | 原因 |
|------|------|------|------|
| 2026-09-13 | —— | 无 | 冻结后未变更 |
