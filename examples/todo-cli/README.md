# 示例运行：todo-cli —— 命令行待办事项工具

> 这是 SpecPilot 流水线的一次**完整级真实演示运行**的产物：需求「做一个命令行待办事项工具，支持增删改查和优先级排序」经过 阶段 1 需求 → 👤确认 SRS → 阶段 2 设计 → 任务拆解 → 冻结测试用例 → 阶段 3 编码 → 阶段 4 测试 → 收敛核对 → 👤最终验收 的完整链路。
>
> 所有"客观裁判"结果均真实执行：单元测试 42/42 通过（`python3 -m unittest` 退出码 0），`compileall` 零错误，NFR 实测达标（100 条待办 `list` 0.026s ≤ 0.5s）。测试一轮全绿，未触发缺陷修复循环（熔断计数 0/5）。

## 看什么

按流水线产物链顺序阅读 `docs/`，可以完整看到"一句话需求如何变成可交付软件"的每一步契约：

| 文件 | 阶段 | 看点 |
|------|------|------|
| `docs/00-constitution.md` | 阶段 0 | 技术栈边界（零第三方依赖）如何在后续阶段被逐条遵守 |
| `docs/01-srs.md` | 阶段 1 | 每条功能需求附带可自动验证的验收标准（如"退出码 2"而非"报错"）；7.2 默认假设表展示"我替你假设了什么" |
| `docs/02-design.md` | 阶段 2 | 模块单向依赖、退出码约定、需求覆盖对照表 |
| `docs/03-tasks.md` | 拆解 | 每个任务的完成判据都能对应到测试用例 ID；预估/实际工时列演示估算闭环 |
| `docs/04-test-cases.md` | 编码前冻结 | 30 个用例只从 SRS/设计反向生成，未看实现；每条带"失效检测点"；需求覆盖矩阵无缺口 |
| `docs/05-dev-doc.md` | 阶段 3 | 与设计"零差异"、42 个单测的模块分布、运行指南 |
| `docs/06-test-report.md` | 阶段 4 | 逐用例结果、NFR 实测数据、收敛核对清单 |
| `docs/lessons.md` | 验收后 | 复盘：模板哪里不顺、下次怎么改 |

此外包含一次**交付后轻量级变更**的演示：`docs/changes/fix-newline-content/`——真实缺陷（内容含换行符破坏列表逐行显示）按轻量级路径走完 spec.md → 冻结用例 → 修复 → 回归（47/47 全绿）→ 增量合入主 SRS，展示 OpenSpec 式按变更归档的组织方式。

## 复现验证（零依赖，任何 Python 3.10+ 机器可跑）

```bash
cd examples/todo-cli

# 单元测试（42 个用例）
python3 -m unittest discover -s tests

# 构建/语法检查
python3 -m compileall -q todo tests todo.py

# 端到端试一把（用 TODO_FILE 隔离，不污染 ~/.todo-cli.json）
export TODO_FILE=$(mktemp -d)/todos.json
python3 todo.py add "写周报" -p high
python3 todo.py add "买咖啡" -p low
python3 todo.py list          # 按优先级排序：高在前
python3 todo.py done 1
python3 todo.py list          # 已完成项 [x] 标注且排最后
python3 todo.py rm 2
python3 todo.py done 99       # 业务错误：退出码 1
echo $?
python3 todo.py add ""        # 用法错误：退出码 2
echo $?
```
