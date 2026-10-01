# AGENTS.md

Codex 等以 AGENTS.md 为项目指令约定的工具，在会话启动时自动读取本文件。

## SpecPilot 完整开发流程

当用户要求"自动开发""完整做一个项目""跑四阶段流水线""跑 SpecPilot"，或希望 AI 端到端完成"需求分析 → 设计 → 编码 → 测试"时：

**阅读 [.agents/skills/spec-pilot/SKILL.md](.agents/skills/spec-pilot/SKILL.md) 并严格遵循其中的流水线执行。**

- 该文档是唯一的流程规范：四阶段规则、两个人工检查点、熔断与变更处理都在其中；各阶段产物格式用同目录 `references/` 下的模板；
- 流程要求机械验证（阶段门禁、退出码采集、熔断计数）时，使用 `orchestrator/specpilot.py`（`gate` / `test` / `reset`）；
- 宿主无子代理能力时，按 SKILL.md"上下文隔离"节的环境降级执行；
- 与上述无关的任务，不受本文件约束。
