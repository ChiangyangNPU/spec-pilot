# SpecPilot 薄编排器（机械层首版）

> 对应 [design-rationale.md](../design-rationale.md) 第 5 节"落地方案"的首版实现。此前整套流程的硬规则（真实运行、熔断 5 轮、收敛核对）都是写给 AI 的承诺；本工具把其中可机械化的三件事变成脚本强制——**阶段门禁、熔断计数、退出码采集**。零第三方依赖，Python 3.10+。

## 它机械化了哪些规则

| 提示词层规则（原靠 AI 自觉） | 机械层实现 |
|------------------------------|------------|
| "每阶段收尾自检产物完整性，补齐才进入下一阶段" | `gate`：产物存在性、必需章节、FR 验收标准列/NFR 验证方式列非空、覆盖矩阵无缺口，由脚本判定，未过不继续 |
| "缺陷修复循环最多 5 轮，超限熔断升级给人" | `test`：失败轮次是状态文件里的计数器，第 5 轮失败即熔断，此后所有测试调用直接拒绝（退出码 42）——第 6 轮在物理上不可能发生 |
| "用户给出新指引后熔断计数清零" | `reset --guidance`：必须携带指引文本并留痕，才清零重入 |
| "构建、Lint、测试真实运行、以退出结果为准" | `test`：命令真实执行、输出直通终端、退出码与轮次写入 `docs/.pipeline-state.json`——报告数字有据可查 |

## 用法（在流水线项目根目录，即 docs/ 所在处）

```bash
# 初始化（创建 docs/ 与状态文件）
python3 orchestrator/specpilot.py init

# 阶段门禁（各阶段收尾时执行，退出码 0 才继续）
python3 orchestrator/specpilot.py gate 1        # SRS 完整性（章节齐全、验收标准/验证方式列非空）
python3 orchestrator/specpilot.py gate 2        # 设计覆盖（覆盖对照表存在、SRS 每条需求有落点）
python3 orchestrator/specpilot.py gate 3        # 编码前一致性（任务/用例存在、覆盖矩阵无缺口）
python3 orchestrator/specpilot.py gate final    # 收敛核对（任务全勾选、结论可交付、无 BLOCKED、熔断已解除）

# 轻量级变更门禁
python3 orchestrator/specpilot.py gate 3 --changes fix-newline-content

# 真实运行测试并采集退出码（输出直通终端）
python3 orchestrator/specpilot.py test -- python3 -m unittest discover -s tests

# 熔断后（连续 5 轮失败），凭用户新指引清零
python3 orchestrator/specpilot.py reset --guidance "用户确认改用方案 B 后重试"

# 查看状态
python3 orchestrator/specpilot.py status
```

**退出码约定**：`0` 通过；`1` 门禁未通过（列出全部缺口）或测试命令自身失败（原样透传子命令退出码）；`42` 熔断触发或熔断期间被拒。

## 状态文件

`docs/.pipeline-state.json`：修复轮次、熔断标志、最近指引、最近 50 条运行历史（时间、命令、退出码）。它是流水线的运行审计记录，随项目提交。

## 边界与后续

- 解析是**宽容的**：只依赖模板的结构特征（表格行、章节标题），不追求完整 Markdown 解析；模板结构大改时需同步调整 `specpilot.py`。
- 自身带单元测试（熔断状态机 + 解析函数）：`python3 orchestrator/tests/test_specpilot.py`。
- design-rationale 第 5 节的另外两件事——**CI 产结果**（报告数字从 CI 拉取而非 AI 填写）与**容器沙箱**（执行安全守则的物理化）——仍为后续增强。
