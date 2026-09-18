# SpecPilot 薄编排器（机械层首版）

> 对应 [design-rationale.md](../design-rationale.md) 第 5 节"落地方案"的首版实现。此前整套流程的硬规则（真实运行、熔断 5 轮、收敛核对）都是写给 AI 的承诺；本工具把其中可机械化的三件事变成脚本强制——**阶段门禁、熔断计数、退出码采集**——并以 **CI 产结果**（自证工作流 + 项目模板）与**容器沙箱**（Docker 强制执行安全边界）补齐 §5 四要点。零第三方依赖，Python 3.10+。

## 它机械化了哪些规则

| 提示词层规则（原靠 AI 自觉） | 机械层实现 |
|------------------------------|------------|
| "每阶段收尾自检产物完整性，补齐才进入下一阶段" | `gate`：产物存在性、必需章节、FR 验收标准列/NFR 验证方式列非空、覆盖矩阵无缺口，由脚本判定，未过不继续 |
| "缺陷修复循环最多 5 轮，超限熔断升级给人" | `test`：失败轮次是状态文件里的计数器，第 5 轮失败即熔断，此后所有测试调用直接拒绝（退出码 42）——第 6 轮在物理上不可能发生 |
| "用户给出新指引后熔断计数清零" | `reset --guidance`：必须携带指引文本并留痕，才清零重入 |
| "构建、Lint、测试真实运行、以退出结果为准" | `test`：命令真实执行、输出直通终端、退出码与轮次写入 `docs/.pipeline-state.json`——报告数字有据可查 |
| "AI 生成的代码真实执行必须有隔离边界"（执行安全守则） | `sandbox.sh`：`--network none`、仅挂载项目目录、只读根文件系统、`--cap-drop ALL`——守则由容器从"不允许"变为"不可能" |
| "流水线绿灯才算数"（结论由谁产出） | 自证 CI 工作流（`.github/workflows/ci.yml`）+ 项目模板（`ci-templates/`）；运行记录 `source` 字段区分 ci/session |

## 用法（在流水线项目根目录，即 docs/ 所在处）

```bash
# 初始化（创建 docs/ 与状态文件）
python3 orchestrator/specpilot.py init

# 阶段门禁（各阶段收尾时执行，退出码 0 才继续）
python3 orchestrator/specpilot.py gate 1        # SRS 完整性（章节齐全、验收标准/验证方式列非空）
python3 orchestrator/specpilot.py gate 2        # 设计覆盖（覆盖对照表存在、SRS 每条需求有落点）
python3 orchestrator/specpilot.py gate 3        # 编码前一致性（任务/用例存在、覆盖矩阵无缺口）
python3 orchestrator/specpilot.py gate final    # 收敛核对（任务全勾选、结论可交付、无 BLOCKED、熔断已解除、新建项目有 README）

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

`docs/.pipeline-state.json`：修复轮次、熔断标志、最近指引、最近 50 条运行历史（时间、命令、退出码、`source`）。它是流水线的运行审计记录，随项目提交。

## CI 产结果（首版）

- **本仓库自证**：[.github/workflows/ci.yml](../.github/workflows/ci.yml) 在每次推送时真实运行——编排器单测、SKILL 模板引用齐全性、示例 5 道门禁、示例测试经 `test` 采集（CI 环境自动记 `source=ci`）并上传状态 artifact。仓库的绿灯是 Actions 跑出来的，不是宣称的。
- **用户项目**：复制 [ci-templates/github-actions-specpilot.yml](ci-templates/github-actions-specpilot.yml) 到项目 `.github/workflows/`，替换构建/测试命令；门禁按流水线当前阶段启用。
- 报告背书：项目配置了 CI 后，`06-test-report.md` 的构建/Lint/测试结论须引用 CI 运行结果；`source` 字段说明每条记录由谁产出。

## 容器沙箱（首版）

```bash
orchestrator/sandbox.sh <项目目录> <命令...>
# 例：跑示例测试（容器内无网络、根文件系统只读、仅见 /work）
orchestrator/sandbox.sh examples/todo-cli python3 -m unittest discover -s tests
```

强制的边界：`--network none`（外联物理不可达）、仅挂载项目目录到 `/work`（项目外不可见）、`--read-only` + tmpfs `/tmp`（可写面收敛）、`--cap-drop ALL` + `no-new-privileges`（无特权可提）、宿主 UID 映射（不留 root 文件）、内存/CPU/PID 限额。需要第三方依赖的项目，构建含依赖的定制镜像（`SPECPILOT_SANDBOX_IMAGE` 覆盖）——依赖安装发生在构建期并留痕，运行期无网。自证 CI 的 sandbox 作业验证"沙箱内测试跑通 + 网络确为不可达"。

## 边界与后续

- 解析是**宽容的**：只依赖模板的结构特征（表格行、章节标题），不追求完整 Markdown 解析；模板结构大改时需同步调整 `specpilot.py`。
- 自身带单元测试（熔断状态机 + 解析函数）：`python3 orchestrator/tests/test_specpilot.py`。
- design-rationale §5 四要点均已首版落地；残余增强：测试报告数字从 CI 系统自动拉取生成（现阶段由执行者引用 CI 结论填写）、远程托管沙箱服务、沙箱定制镜像的构建约定。
