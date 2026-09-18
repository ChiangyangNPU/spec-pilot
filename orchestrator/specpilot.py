#!/usr/bin/env python3
"""SpecPilot 薄编排器——把流水线的关键纪律从提示词层落到机械层。

对应 design-rationale.md 第 5 节"落地方案"的首版实现，只做三件事：

1. 阶段门禁（gate）：产物存在性与完整性由脚本校验，不靠 AI 自查——
   gate 1 SRS 完整性 / gate 2 设计覆盖 / gate 3 编码前一致性（含轻量级 --changes）/
   gate final 收敛核对。
2. 熔断计数（test）：缺陷修复轮次是脚本里的状态而非 AI 的记忆——
   连续第 5 轮失败即熔断，此后所有测试调用直接拒绝（退出码 42），
   直到用户给出新指引并执行 reset 清零重入（对应 SKILL.md 熔断规则）。
3. 退出码采集（test）：构建/测试命令真实运行（输出直通终端），
   结果与轮次写入 docs/.pipeline-state.json——报告数字有据可查，
   "Agent 说做完了不算数"。

零第三方依赖，Python 3.10+。在流水线项目根目录（docs/ 所在处）运行。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_STATE = Path("docs/.pipeline-state.json")
MAX_ROUNDS = 5
EXIT_GATE_FAIL = 1
EXIT_BREAKER = 42
BREAKER_HINT = (
    "熔断触发：缺陷修复循环已达上限，停止循环。"
    "向用户报告迭代历史、仍未通过的用例与根因分析；"
    "用户给出新指引后执行 reset --guidance <指引> 清零重入。"
)


# ---------- 状态 ----------
def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"rounds": 0, "tripped": False, "last_guidance": None, "history": []}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_test_result(state: dict, exit_code: int, command: str,
                      max_rounds: int = MAX_ROUNDS, ts: str | None = None) -> tuple[dict, dict]:
    """纯函数：把一次真实运行的退出码结算进状态。成功即循环结束（轮次清零）；
    失败轮次 +1，达到上限置熔断。返回 (新状态, 历史条目)。"""
    new = json.loads(json.dumps(state))
    entry = {
        "ts": ts or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "command": command,
        "exit_code": exit_code,
    }
    if exit_code == 0:
        new["rounds"] = 0
        new["tripped"] = False
    else:
        new["rounds"] = state.get("rounds", 0) + 1
        if new["rounds"] >= max_rounds:
            new["tripped"] = True
            entry["tripped"] = True
    new["history"] = (state.get("history", []) + [entry])[-50:]
    return new, entry


# ---------- Markdown 解析（宽容：只依赖模板的结构特征） ----------
def read_doc(path: Path, problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"缺少产物：{path}")
        return None
    return path.read_text(encoding="utf-8")


def extract_section(text: str, keyword: str) -> str:
    """取第一个标题含 keyword 的 ## 节正文（到下一个 ## 为止）。"""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("##") and keyword in ln:
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    for ln in lines[start:]:
        if ln.startswith("## "):
            break
        out.append(ln)
    return "\n".join(out)


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


def requirement_ids(text: str) -> list[str]:
    """从 SRS 表格行提取 FR-x / NFR-x 编号。"""
    return sorted(set(re.findall(r"^\|\s*((?:FR|NFR)-\d+)\b", text, re.M)))


def srs_requirement_problems(srs: str) -> list[str]:
    """每条 FR 必须有非空验收标准列，每条 NFR 必须有非空验证方式列。"""
    problems = []
    for cells in table_rows(srs):
        if not cells:
            continue
        head = cells[0]
        if re.fullmatch(r"FR-\d+", head):
            if len(cells) < 5 or not cells[-1]:
                problems.append(f"SRS {head}：验收标准列缺失或为空（流水线闭环的前提）")
        elif re.fullmatch(r"NFR-\d+", head):
            if len(cells) < 4 or not cells[-1]:
                problems.append(f"SRS {head}：验证方式列缺失或为空")
    return problems


def coverage_gaps(tc_text: str) -> tuple[list[str], bool]:
    """检查覆盖矩阵：返回 (缺口行列表, 是否找到矩阵节)。"""
    sec = extract_section(tc_text, "覆盖矩阵")
    if not sec.strip():
        return [], False
    gaps = [
        ln.strip()
        for ln in sec.splitlines()
        if re.match(r"^\|\s*(?:FR|NFR|AC|A)-", ln.strip())
        and ("—" in ln or "❌" in ln or "缺口" in ln)
    ]
    return gaps, True


# ---------- 门禁 ----------
def gate_1(docs: Path, problems: list[str]) -> None:
    srs = read_doc(docs / "01-srs.md", problems)
    if srs is None:
        return
    for kw in ["项目概述", "用例", "业务流程", "功能需求", "非功能需求", "系统边界", "待确认"]:
        if not re.search(rf"^##.*{kw}", srs, re.M):
            problems.append(f"SRS 缺少章节：{kw}")
    problems += srs_requirement_problems(srs)


def gate_2(docs: Path, problems: list[str]) -> None:
    srs = read_doc(docs / "01-srs.md", problems)
    design = read_doc(docs / "02-design.md", problems)
    if srs is None or design is None:
        return
    if "需求覆盖对照表" not in design:
        problems.append("设计文档缺少“需求覆盖对照表”")
    for rid in requirement_ids(srs):
        if not re.search(rf"\b{re.escape(rid)}\b", design):
            problems.append(f"{rid} 未出现在设计文档（覆盖对照表须逐条给出落点）")


def gate_3(docs: Path, problems: list[str], changes: str | None) -> None:
    if changes:
        base = docs / "changes" / changes
        spec = read_doc(base / "spec.md", problems)
        tc = read_doc(base / "04-test-cases.md", problems)
        if spec is not None and "验收标准" not in spec:
            problems.append("spec.md 缺少验收标准")
    else:
        read_doc(docs / "03-tasks.md", problems)
        tc = read_doc(docs / "04-test-cases.md", problems)
        srs = read_doc(docs / "01-srs.md", problems)
        if tc is not None and srs is not None:
            for rid in requirement_ids(srs):
                if not re.search(rf"\b{re.escape(rid)}\b", tc):
                    problems.append(f"{rid} 在冻结用例中无对应用例")
    if tc is not None:
        gaps, found = coverage_gaps(tc)
        if not found:
            problems.append("测试用例缺少“覆盖矩阵”节")
        problems += [f"覆盖缺口：{g}" for g in gaps]


def gate_final(docs: Path, problems: list[str]) -> None:
    read_doc(docs / "00-constitution.md", problems)
    tasks = read_doc(docs / "03-tasks.md", problems)
    tc = read_doc(docs / "04-test-cases.md", problems)
    report = read_doc(docs / "06-test-report.md", problems)
    if tasks is not None and "☐" in tasks:
        problems.append("任务清单存在未勾选项（☐）——任务未全部完成不得交付")
    if tc is not None:
        gaps, _ = coverage_gaps(tc)
        problems += [f"覆盖缺口：{g}" for g in gaps]
    if report is not None:
        m = re.search(r"^-\s*\*\*结论\*\*[:：]\s*(.+)$", report, re.M)
        if not m:
            problems.append("测试报告缺少结论行")
        elif "可交付" not in m.group(1):
            problems.append(f"测试报告结论未达可交付：{m.group(1).strip()}")
        blocked_rows = [
            ln.strip()
            for ln in extract_section(report, "BLOCKED").splitlines()
            if re.match(r"^\|\s*TC-", ln.strip())
        ]
        if blocked_rows:
            problems.append(f"存在未处理的 BLOCKED 用例 {len(blocked_rows)} 条——须补跑或经用户明确接受")
    state = load_state(DEFAULT_STATE)
    if state.get("tripped"):
        problems.append("熔断未解除：须由用户新指引 reset 后才能进入交付")
    dev_doc = read_doc(docs / "05-dev-doc.md", problems)
    if dev_doc is not None and "从零新建" in dev_doc and not Path("README.md").exists():
        problems.append("开发文档标注从零新建，但项目根缺少 README.md——README 是交付物的一部分")


# ---------- 子命令 ----------
def cmd_init(_args) -> int:
    docs = Path("docs")
    docs.mkdir(exist_ok=True)
    if not DEFAULT_STATE.exists():
        save_state(DEFAULT_STATE, load_state(DEFAULT_STATE))
    print(f"✅ 已就绪：{docs}/ 与状态文件 {DEFAULT_STATE}")
    return 0


def cmd_gate(args) -> int:
    docs = Path("docs")
    problems: list[str] = []
    if args.phase == "1":
        gate_1(docs, problems)
    elif args.phase == "2":
        gate_2(docs, problems)
    elif args.phase == "3":
        gate_3(docs, problems, args.changes)
    elif args.phase == "final":
        gate_final(docs, problems)
    label = "轻量级变更 " + args.changes if args.changes else f"阶段 {args.phase}"
    if problems:
        print(f"❌ 门禁未通过（{label}）：")
        for p in problems:
            print(f"  - {p}")
        return EXIT_GATE_FAIL
    print(f"✅ 门禁通过（{label}）：产物完整、覆盖无缺口")
    return 0


def cmd_test(args) -> int:
    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("用法：specpilot.py test -- <构建/测试命令...>", file=sys.stderr)
        return EXIT_GATE_FAIL
    state = load_state(DEFAULT_STATE)
    if state.get("tripped"):
        print(f"⛔ {BREAKER_HINT}", file=sys.stderr)
        print(f"   上一轮状态：熔断（{state.get('rounds', '?')} 轮失败），"
              f"最近指引：{state.get('last_guidance') or '（无记录）'}", file=sys.stderr)
        return EXIT_BREAKER
    proc = subprocess.run(cmd)  # 输出直通终端：结果客观可见
    command = " ".join(cmd)
    state, entry = apply_test_result(state, proc.returncode, command)
    save_state(DEFAULT_STATE, state)
    if proc.returncode == 0:
        print(f"✅ 退出码 0（轮次清零）｜已记录：{command}")
        return 0
    print(f"❌ 退出码 {proc.returncode}｜修复轮次 {state['rounds']}/{MAX_ROUNDS}｜已记录：{command}")
    if state.get("tripped"):
        print(f"⛔ {BREAKER_HINT}", file=sys.stderr)
        return EXIT_BREAKER
    return proc.returncode


def cmd_reset(args) -> int:
    state = load_state(DEFAULT_STATE)
    state["rounds"] = 0
    state["tripped"] = False
    state["last_guidance"] = args.guidance
    state["history"] = (state.get("history", []) + [{
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "action": "reset",
        "guidance": args.guidance,
    }])[-50:]
    save_state(DEFAULT_STATE, state)
    print(f"✅ 熔断已清零，凭新指引重新进入修复循环：「{args.guidance}」")
    return 0


def cmd_status(_args) -> int:
    state = load_state(DEFAULT_STATE)
    docs = Path("docs")
    print(f"修复轮次：{state.get('rounds', 0)}/{MAX_ROUNDS}｜熔断：{'是' if state.get('tripped') else '否'}")
    print(f"最近指引：{state.get('last_guidance') or '（无）'}")
    for entry in state.get("history", [])[-3:]:
        if entry.get("action") == "reset":
            label = f"reset  {entry.get('guidance', '')}"
        else:
            label = f"exit={entry.get('exit_code')}  {entry.get('command', '')}"
        print(f"  {entry.get('ts')}  {label}")
    print("产物：", " ".join(
        f"{p.name}{'✓' if p.exists() else '✗'}" for p in [
            docs / "00-constitution.md", docs / "01-srs.md", docs / "02-design.md",
            docs / "03-tasks.md", docs / "04-test-cases.md", docs / "05-dev-doc.md",
            docs / "06-test-report.md",
        ]))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specpilot",
        description="SpecPilot 薄编排器：阶段门禁 + 熔断计数 + 退出码采集（机械层首版）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("gate", help="阶段门禁：校验产物完整性与覆盖")
    g.add_argument("phase", choices=["1", "2", "3", "final"], help="1 SRS / 2 设计 / 3 编码前 / final 收敛核对")
    g.add_argument("--changes", help="轻量级路径：校验 docs/changes/<变更名>/（配合 gate 3）")

    t = sub.add_parser("test", help="真实运行构建/测试命令并采集退出码")
    t.add_argument("cmd", nargs=argparse.REMAINDER, help="test -- <命令...>")

    r = sub.add_parser("reset", help="熔断后凭用户新指引清零重入")
    r.add_argument("--guidance", required=True, help="用户给出的新指引（留痕）")

    sub.add_parser("status", help="查看流水线状态与产物清单")
    sub.add_parser("init", help="初始化 docs/ 与状态文件")

    args = parser.parse_args(argv)
    return {"init": cmd_init, "gate": cmd_gate, "test": cmd_test,
            "reset": cmd_reset, "status": cmd_status}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
