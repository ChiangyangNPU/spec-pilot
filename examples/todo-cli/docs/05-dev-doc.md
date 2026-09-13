# 开发文档 —— 命令行待办事项工具

> 产生于阶段 3（编码中同步编写、编码完成后定稿）。记录"实际实现了什么"，与 docs/02-design.md 互补。

## 1. 工程背景

- **工程类型**：从零新建
- **运行环境**：Python 3.13.13 / macOS（NFR-2 在该环境验证；代码仅用 3.10+ 稳定特性）

## 2. 实现概述

与设计文档的关键差异：**无差异**——模块划分、接口签名、数据结构、退出码均按 `docs/02-design.md` 实现。

| 设计约定 | 实际实现 | 差异原因 |
|----------|----------|----------|
| （无） | 与设计一致 | —— |

## 3. 实际目录结构

```
todo-cli/
├── todo/                 # 实现包
│   ├── __init__.py
│   ├── models.py        # Todo、Priority、TodoError（最底层，无内部依赖）
│   ├── storage.py       # Storage：JSON 原子读写（依赖 models）
│   ├── core.py          # TodoApp：业务规则（依赖 models、storage）
│   └── cli.py           # argparse 子命令 + 退出码映射（依赖 core、models、storage）
├── tests/                # 单元测试（42 个用例）
│   ├── test_models.py   # 8 个：优先级、排序键、序列化
│   ├── test_storage.py   # 4 个：空文件、roundtrip、损坏 JSON
│   ├── test_core.py      # 16 个：五个业务方法 × 正常/边界/异常
│   └── test_cli.py       # 14 个：subprocess 真实进程端到端
├── todo.py               # 启动脚本（python todo.py <子命令>）
└── docs/                 # 本产物链（00~06 + lessons）
```

## 4. 实现类图

与设计类图一致（见 `docs/02-design.md` 第 4 节），无偏差。

## 5. 接口/模块实现清单

| 设计接口/模块 | 实现位置（文件） | 状态 | 备注 |
|---------------|------------------|------|------|
| Priority 枚举 | todo/models.py | 已完成 | Enum 成员携带 (key, 中文标签, 排序权重) 三元组 |
| Todo / TodoError | todo/models.py | 已完成 | dataclass；TodoError 带 exit_code |
| Storage.load/save | todo/storage.py | 已完成 | save 采用临时文件 + `os.replace` 原子写 |
| TodoApp.add/list_sorted/done/remove/set_priority | todo/core.py | 已完成 | 校验与错误码全部按设计第 9 节 |
| CLI 五个子命令 | todo/cli.py | 已完成 | TodoError → stderr + 对应退出码 |

## 6. 单元测试清单

| 测试文件 | 被测类/模块 | 用例数 | 覆盖场景 |
|----------|-------------|--------|----------|
| test_models.py | Priority、Todo | 8 | 正常（标签/构造/roundtrip）、边界（同优先级排序）、异常（非法优先级、损坏字典） |
| test_storage.py | Storage | 4 | 正常（roundtrip）、边界（文件不存在）、异常（损坏 JSON 不清空原文件） |
| test_core.py | TodoApp | 16 | 五个方法的正常路径 + 边界（ID 递增、完成态排序）+ 异常（空内容、非法优先级、ID 不存在、重复完成） |
| test_cli.py | cli.main 端到端 | 14 | 子进程真实执行：成功输出、全部错误路径的退出码 1/2、TODO_FILE 环境变量 |

合计 42 个用例，`python3 -m unittest discover -s tests` 一次全绿（42/42，0.74s）。

## 7. 本地运行指南

```bash
cd examples/todo-cli

# 无需安装任何依赖（零第三方库）

# 使用（数据默认存 ~/.todo-cli.json，可用 TODO_FILE 覆盖）
python3 todo.py add "写周报" -p high
TODO_FILE=/tmp/t.json python3 todo.py list

# 单元测试
python3 -m unittest discover -s tests -v

# 构建/语法检查
python3 -m compileall -q todo tests todo.py
```

## 8. 开发记录

| 日期 | 问题/决策 | 处理方式 |
|------|-----------|----------|
| 2026-09-13 | JSON 写入若直接覆盖，进程中断会留下半截文件 | 采用临时文件 + `os.replace` 原子写（设计第 6 节已约定，落实时确认） |
| 2026-09-13 | CLI 测试需要隔离，避免污染真实 `~/.todo-cli.json` | 测试统一通过 `TODO_FILE` 环境变量指向临时目录（TC-30 机制同时服务于测试隔离） |
| 2026-09-13 | 覆盖率无法测量 | 零依赖约束下不引入 coverage 工具，测试报告中如实标注"未测量" |
