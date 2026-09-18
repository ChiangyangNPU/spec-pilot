# SpecPilot 🛩️

**中文** | [English](README_EN.md)

> 规格驱动的 AI 四阶段自动开发流水线：**AI 执行需求 → 设计 → 编码 → 测试全部阶段，人只在两个节点介入——确认需求、最终验收。**

```mermaid
flowchart LR
    A["👤 提出需求"] --> B["阶段1 需求分析"]
    B --> H1{"👤 确认 SRS"}
    H1 --> C["阶段2 设计"]
    C --> D["任务拆解"]
    D --> E["冻结测试用例"]
    E --> F["阶段3 编码"]
    F --> G["阶段4 测试"]
    G -- "不通过：缺陷回传修复<br/>（最多5轮，超限熔断）" --> F
    G -- 通过 --> H["收敛核对"]
    H --> I{"👤 最终验收"}
    I -- 通过 --> J(["交付"])
```

## 这是什么

本仓库包含五部分：

| 目录/文件 | 内容 |
|-----------|------|
| [.agents/skills/spec-pilot/](.agents/skills/spec-pilot/) | **SpecPilot skill**——ZCode 中的可执行流水线：`SKILL.md` 主流程 + 6 份带序号的阶段产物模板（含编码前冻结的测试用例模板）+ 编码自检清单 + 轻量级变更模板 |
| [orchestrator/](orchestrator/README.md) | **薄编排器**——机械层：阶段门禁、熔断计数、退出码采集由脚本强制（`gate`/`test`/`reset`），"真实运行""最多 5 轮"从提示词承诺变为物理约束；含 GitHub Actions 自证工作流与项目 CI 模板、容器沙箱执行器（无网络、只读根、仅挂载项目目录） |
| [examples/todo-cli/](examples/todo-cli/) | **一次完整级真实运行的产物**——CLI 待办工具从 SRS 到测试报告的全链产物，代码与测试真实跑通（42/42 单测全绿），展示"跑完长什么样" |
| [design-rationale.md](design-rationale.md) | 设计理念文档：为什么这样设计、关键决策（角色分离、客观裁判、熔断）的思考 |
| [software-development-phases/](software-development-phases/) | 传统软件工程流程八篇（可行性 → 需求 → 设计 → 编码 → 测试 → 部署 → 维护 + 支持性过程），含 Mermaid 图。**定位是给人看的背景材料**——理解阶段划分的来龙去脉；流水线执行时并不读取它，AI 角色的工作规范以 `SKILL.md` 及其模板为准 |

## 核心理念

1. **文档是阶段契约**：每阶段产出物是下一阶段的唯一输入——SRS → 设计 → 任务清单 → 代码 → 测试报告，任何变更沿文档链向后传播，不允许只改代码。
2. **角色分离防"自我认同"**：测试用例在编码前从需求反向生成并冻结（不看代码实现），AI 写的代码由"只认需求"的用例来验证。
3. **CI 是客观裁判**：构建、Lint、单元测试必须真实运行、以退出结果为准，AI 自己说"做完了"不算数。
4. **熔断兜底**：缺陷修复循环最多 5 轮，不收敛就升级给人。
5. **人保留两个必答节点**：需求确认（业务意图的真值来源）+ 最终验收（责任主体）。

流程吸收了三个开源框架的机制并做了本地化：

- [GitHub Spec Kit](https://github.com/github/spec-kit)：constitution（项目约束）、tasks（任务拆解）、analyze（一致性检查）、converge（收敛核对）
- [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)：right-sizing（流程分级）、验收后复盘
- [OpenSpec](https://github.com/Fission-AI/OpenSpec)：按变更组织产物、增量归档

## 使用方法

前提：使用支持 Agent Skills 的 AI 编码工具（本 skill 按 ZCode 规范编写）。

```text
# 从零开发
/spec-pilot 做一个命令行待办事项工具，支持增删改查和优先级排序

# 给已有项目加功能（在项目目录下）
/spec-pilot 给这个项目加一个导出 Excel 的功能

# 小改动（自动走轻量级路径）
/spec-pilot 修复：列表页输入特殊字符会崩溃

# 全自动模式（跳过 SRS 确认检查点）
/spec-pilot 全自动运行，中途别问我，做一个 xxx
```

也可以用自然语言触发："自动开发""AI 全流程做一个 xxx""跑 SpecPilot"。

跑完后项目里会留下完整产物链（`docs/` 目录）：

```
docs/
├── 00-constitution.md   # 项目约束（技术栈边界、规范要点、质量底线）
├── 01-srs.md            # 需求规格说明书（用例图、业务流程图、验收标准）
├── 02-design.md         # 设计文档（架构图、类图、时序图、E-R 图）
├── 03-tasks.md          # 任务清单（逐项勾选推进）
├── 04-test-cases.md     # 测试用例（编码前从需求反向生成并冻结）
├── 05-dev-doc.md        # 开发文档（实现结构、与设计差异、运行指南）
├── 06-test-report.md    # 测试报告（每轮结果、缺陷、趋势）
├── lessons.md           # 复盘记录（验收后追加，下次启动先读）
└── changes/<变更名>/     # 交付后增量变更的轻量级产物（spec.md + 04 + 06，完成后合入主文档）
```

想先看一次真实运行的完整产物链？见 [examples/todo-cli/](examples/todo-cli/)——从一句话需求（"做一个命令行待办事项工具，支持增删改查和优先级排序"）到 8 份产物文档加可运行代码，单元测试 42/42 全绿。

## 定制

修改这套流程时遵循**三层归位**，防止规则越堆越厚、稀释执行：

1. **判断性规则**（怎么权衡、何时升级、何时豁免）→ 写进 [SKILL.md](.agents/skills/spec-pilot/SKILL.md) 正文；
2. **结构性要求**（该有哪些节、哪些列、哪些自检项）→ 下沉到 `references/` 对应模板的"产出物自检"清单，不占正文注意力；
3. **可机械判定的**（产物存在性、非空、勾选状态、退出码、覆盖矩阵无缺口）→ 下沉到 [orchestrator](orchestrator/README.md) 的 `gate`，由脚本强制，正文一个字不提。

每想往 SKILL.md 正文加一条规则，先问能不能降级到后两层；定期回顾正文长度。

## License

MIT
