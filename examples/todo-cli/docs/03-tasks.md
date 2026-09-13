# 任务清单 —— 命令行待办事项工具

> 产生于任务拆解环节（设计后、编码前）。以 docs/02-design.md 为依据拆解。

## 任务清单

| # | 任务 | 目标（做什么） | 涉及模块 | 完成判据（怎么算做完） | 依赖 | 状态 |
|---|------|----------------|----------|------------------------|------|------|
| T1 | 数据模型与优先级枚举 | 实现 Todo、Priority、TodoError；sort_key 定义 FR-2 排序权重 | models.py | `test_models.py` 全绿：三档标签、from_str 非法值、sort_key 顺序（TC-01/02/03） | 无 | ☑ |
| T2 | JSON 持久化 | Storage 读/写/原子保存；TODO_FILE 覆盖；损坏文件报错不清空 | storage.py | `test_storage.py` 全绿：空文件初始化、roundtrip、损坏 JSON 抛错（TC-15/16/17） | T1 | ☑ |
| T3 | 业务规则 | TodoApp 五个方法：add/done/remove/set_priority/list_sorted，含全部校验 | core.py | `test_core.py` 全绿：正常路径 + 不存在 ID + 重复完成 + 非法优先级 + 排序（TC-04~14 对应核心逻辑） | T2 | ☑ |
| T4 | CLI 子命令与退出码 | argparse 五个子命令；TodoError→stderr+退出码；成功输出到 stdout | cli.py、todo.py | `test_cli.py` 全绿：各命令成功输出、错误路径退出码 1/2（TC-18~29） | T3 | ☑ |
| T5 | 端到端验收 | 完整跑一遍 UC-1→UC-5 主流程 + NFR 验证 | 全部 | 阶段 4 全部测试用例通过；NFR-1 实测 ≤ 0.5s；NFR-3 检查零第三方 import | T1~T4 | ☑ |

## 任务与需求对照

| 需求编号 | 由哪些任务实现 |
|----------|----------------|
| FR-1 | T1（数据结构）、T3（add 校验）、T4（add 子命令） |
| FR-2 | T1（sort_key）、T3（list_sorted）、T4（list 输出） |
| FR-3 | T3（done）、T4（done 子命令） |
| FR-4 | T3（remove）、T4（rm 子命令） |
| FR-5 | T3（set_priority）、T4（pri 子命令） |
| FR-6 | T2（Storage + TODO_FILE） |
| NFR-1 | T5（性能实测） |
| NFR-2 | T5（本机真实执行） |
| NFR-3 | T1~T4（零依赖实现）、T5（验证） |

> 示例运行说明：状态列为编码阶段逐项勾选后的最终形态。
