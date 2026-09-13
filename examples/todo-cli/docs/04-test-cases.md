# 测试用例（编码前冻结）—— 命令行待办事项工具

> 产生于"冻结测试用例"环节（设计后、编码前）。仅依据 docs/01-srs.md 与 docs/02-design.md 生成，未参考任何实现代码。执行中发现用例本身有错须修正时，在文末变更记录注明原因。

## 1. 单元测试边界约定

FR-1~FR-5 的行为通过 CLI 层用例（TC-18 起）端到端验证；TC-04~TC-17 为对应业务/存储层单元测试，覆盖正常、边界、异常三类场景（对应 00-constitution 质量底线）。

## 2. 测试用例表

### 单元测试（unittest）

| 用例 ID | 来源需求 | 前置条件 | 步骤 | 输入 | 预期结果 |
|---------|----------|----------|------|------|----------|
| TC-01 | FR-1/FR-5 | 无 | 读取三档优先级中文标签 | Priority.HIGH/NORMAL/LOW.label() | 分别为 `高`、`普通`、`低` |
| TC-02 | FR-1/FR-5 | 无 | 用字符串构造优先级 | from_str("high"/"normal"/"low") | 返回对应枚举成员 |
| TC-03 | FR-2 | 无 | 构造不同优先级/完成状态/ID 的 Todo，比较 sort_key | (done, priority权重, -id) 组合 | 未完成 < 已完成；high 权重 < normal < low；同级 id 小者在前 |
| TC-04 | FR-1 | 空存储 | add 内容+默认优先级 | ("写周报", None) | 返回 Todo id=1、priority=NORMAL、done=False |
| TC-05 | FR-1 | 空存储 | add 自定义优先级 | ("买咖啡", HIGH) | priority=HIGH |
| TC-06 | FR-1 | 无 | add 空内容 | ("", None) | 抛 TodoError，exit_code=2 |
| TC-07 | FR-2 | 已有 low/normal/high 各一条未完成 | list_sorted | —— | 顺序为 high、normal、low 对应内容（ID 升序同优先级） |
| TC-08 | FR-2 | 同优先级两条（ID 1、2） | list_sorted | —— | ID 1 在 ID 2 前 |
| TC-09 | FR-3 | #1 未完成 | done(1) | —— | done=True 且持久化后 reload 仍为 True |
| TC-10 | FR-3 | 无 | done(99) | —— | 抛 TodoError exit_code=1 |
| TC-11 | FR-3 | #1 已完成 | 再次 done(1) | —— | 抛 TodoError exit_code=1 |
| TC-12 | FR-4 | #1 存在 | remove(1) | —— | 列表为空，返回被删 Todo |
| TC-13 | FR-4 | 无 | remove(99) | —— | 抛 TodoError exit_code=1 |
| TC-14 | FR-5 | #1 存在 | set_priority(1, LOW) | —— | priority=LOW |
| TC-15 | FR-6 | 文件不存在 | Storage.load() | 任意路径 | 返回空列表，不报错 |
| TC-16 | FR-6 | 已保存若干 Todo | save 后再 load | —— | roundtrip 后字段全部一致 |
| TC-17 | FR-6 | 文件内容为非法 JSON | load() | `{"broken":` | 抛 TodoError（exit_code=1），不清空原文件 |

### CLI 端到端用例（真实进程执行）

| 用例 ID | 来源需求 | 前置条件 | 步骤 | 输入 | 预期结果 |
|---------|----------|----------|------|------|----------|
| TC-18 | FR-1 | `TODO_FILE` 指向临时文件 | 执行 add | `todo add "写周报" -p high` | 退出码 0；stdout 含 `#1 [高] 写周报` |
| TC-19 | FR-1 | 同上 | add 空内容 | `todo add ""` | 退出码 2；stderr 非空 |
| TC-20 | FR-1 | 同上 | add 非法优先级 | `todo add "x" -p urgent` | 退出码 2 |
| TC-21 | FR-2 | 已添加 low/normal/high 三条 | list | `todo list` | 退出码 0；三行顺序 high→normal→low |
| TC-22 | FR-2 | 空存储 | list | `todo list` | 退出码 0；stdout 为 `暂无待办` |
| TC-23 | FR-3 | #1 存在且未完成 | done | `todo done 1` | 退出码 0；随后 list 该行含 `[x]` 且排在未完成之后 |
| TC-24 | FR-3 | #1 不存在 | done | `todo done 99` | 退出码 1；stderr 含"不存在" |
| TC-25 | FR-4 | #1 存在 | rm | `todo rm 1` | 退出码 0；随后 list 为 `暂无待办` |
| TC-26 | FR-4 | #1 不存在 | rm | `todo rm 99` | 退出码 1 |
| TC-27 | FR-5 | #1 存在 | pri | `todo pri 1 low` | 退出码 0；随后 list 该行含 `[低]` |
| TC-28 | FR-5 | #1 不存在 | pri | `todo pri 99 high` | 退出码 1 |
| TC-29 | FR-5 | #1 存在 | 非法优先级 | `todo pri 1 urgent` | 退出码 2 |
| TC-30 | FR-6 | 环境变量已设 | add 后读文件 | `TODO_FILE=/tmp/x.json todo add "a"` | `/tmp/x.json` 存在且为合法 JSON 数组 |

## 3. 需求覆盖矩阵

| 需求编号 | 覆盖用例 |
|----------|----------|
| FR-1 | TC-01、TC-02、TC-04、TC-05、TC-06、TC-18、TC-19、TC-20 |
| FR-2 | TC-03、TC-07、TC-08、TC-21、TC-22 |
| FR-3 | TC-09、TC-10、TC-11、TC-23、TC-24 |
| FR-4 | TC-12、TC-13、TC-25、TC-26 |
| FR-5 | TC-02、TC-14、TC-27、TC-28、TC-29 |
| FR-6 | TC-15、TC-16、TC-17、TC-30 |
| NFR-1 | 验证任务（测试报告第 7 节实测，不设固定用例编号） |
| NFR-2 | 验证任务（本机 Python 3.13 / macOS 真实执行全部用例即为验证） |
| NFR-3 | 验证任务（测试报告第 7 节：检查零第三方 import + 全新目录 unittest 直接跑通） |

矩阵核对结论：6 条功能需求全部有 ≥3 个用例覆盖；3 条 NFR 各有明确验证方式，无遗漏。

## 4. 用例变更记录

| 日期 | 用例 | 变更 | 原因 |
|------|------|------|------|
| 2026-09-13 | —— | 无 | 冻结后未发生变更 |
