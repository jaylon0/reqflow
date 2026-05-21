# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

ReqFlow 是一个 **AI Engineering Harness**——从需求到交付的完整工程化框架。它不调用模型，而是编排模型。通过六大核心能力把 AI 编码从即兴发挥变成可观察、可恢复、可审计的工程流程：

1. **上下文管理** — 模型到底看到了什么
2. **工具系统** — 模型到底能做什么
3. **执行编排** — 模型下一步该做什么
4. **状态与记忆** — 系统如何跨步骤保持连续性
5. **评估与观测** — 系统怎么知道自己做得对不对
6. **约束与恢复** — 出错了怎么办，怎么避免跑偏

## 技术栈

- Python 3.10+
- YAML 工作流定义
- MCP（Model Context Protocol）可选依赖

## 常用命令

```bash
# 安装
pip install -e .              # 基础安装
pip install -e ".[mcp]"       # 含 MCP 依赖
pip install -e ".[all]"       # 全部依赖

# 测试
python -m pytest tests/ -v                          # 全部测试
python -m pytest tests/test_engine.py -v            # 单个测试
python -m pytest tests/test_engine.py::test_name -v # 单个用例

# CLI
reqflow run <requirement> --workflow main-flow
reqflow status <run-dir>
reqflow dashboard <run-dir>
reqflow list-runtimes

# MCP Server
python -m reqflow.runner.mcp_server
```

## 架构概览

```
reqflow/
├── core/                   # 核心模块
│   ├── engine.py           # Engine — 执行引擎，驱动 workflow
│   ├── state_manager.py    # StateManager — state.json、checkpoint、memory
│   ├── tracer.py           # Tracer — 执行追踪
│   ├── tool_bridge.py      # ToolBridge — 工具调用桥接
│   ├── guardrails.py       # Guardrails — 约束检查
│   ├── workflow_loader.py  # WorkflowLoader — 加载 YAML 工作流
│   ├── runtime_config.py   # RuntimeConfig — runtime 配置模型
│   ├── registry.py         # RuntimeRegistry — runtime 注册表
│   ├── context_adapter.py  # ContextAdapter — 上下文适配
│   ├── session.py          # Session — 会话管理
│   └── graph.py            # Graph/Node/Edge — 图编排
├── runner/                 # 运行时入口
│   ├── cli.py              # CLI 子命令
│   ├── mcp_server.py       # MCP Server 实现
│   ├── dashboard.py        # Dashboard 可视化
│   └── host_task.py        # Host Task CLI fallback
├── runtime/providers/      # Runtime 配置（YAML）
├── workflows/              # 工作流定义
├── orchestration/          # 编排文档
├── constraints/            # 约束文档
├── evaluation/             # 评估文档
├── state/                  # 状态文档
└── tests/                  # 测试套件
```

---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 2.5 SOLID & DRY

**SOLID principles — apply when designing components, classes, and functions:**

- **S (Single Responsibility):** Each component, class, or function owns exactly one concern.
- **O (Open/Closed):** Extend behavior without modifying existing code.
- **L (Liskov Substitution):** Subtypes must be fully substitutable for their base types.
- **I (Interface Segregation):** Prefer small, focused interfaces over "fat" ones.
- **D (Dependency Inversion):** Depend on abstractions, not concrete implementations.

**DRY (Don't Repeat Yourself):**

Identify and eliminate duplicated logic. Before writing new code, search for an existing similar implementation — reuse or extend it instead of creating a duplicate. See also: Section 3 (Surgical Changes) for when *not* to refactor existing code unnecessarily.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 3.5 Mandatory Rules as Trackable Todos

**When a skill defines mandatory rules, convert them to todos immediately.**

Before starting any task:
- Scan the active skill's ⛔ mandatory rules section.
- Add each required step as a todo item — including pre-coding checks AND post-coding deliverables.
- The final todo MUST always be: "逐条核对强制规则并输出合规结果" (or equivalent compliance check).

Do NOT mark all todos complete without verifying each mandatory rule was executed. Completing code is not completing the task — completing all mandatory steps is completing the task.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

**Before defining success criteria, complete two phases:**

- **Phase 0 – Understand:** Review the existing code/material thoroughly. Identify where KISS, YAGNI, DRY, and SOLID principles are already applied or violated. Do not skip this phase for non-trivial tasks.
- **Phase 1 – Plan:** Define the task scope and measurable outcomes. Prioritize applying principles to improve existing code over adding new features blindly.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Reporting Protocol

**Only generate a summary report when explicitly asked.**

When a report IS requested, include:
- Core tasks completed this iteration and their concrete outcomes.
- How KISS, YAGNI, DRY, SOLID were applied and the benefit gained (e.g., "extracted duplicate logic into shared helper — DRY").
- Challenges encountered and how they were resolved.
- Clear next steps and recommendations.

When NOT requested: skip the summary entirely. Deliver the change and stop.

**Conciseness vs. Mandatory Deliverables:**

Conciseness means eliminating filler, not skipping mandatory deliverables. If a skill explicitly requires an output (e.g. a compliance report), that output is mandatory regardless of conciseness guidelines. "No report files" means do not write files to disk — it does not mean suppress required outputs from the conversation.

## 6. Language

**Always respond in Chinese.** Use Chinese for all explanations, comments, and communications with the user. Technical terms and code identifiers should remain in their original form.

---

# Communication Style

1. **Communicate in Chinese.** Always respond in Chinese for all explanations, comments, and conversations. Technical terms and code identifiers remain in their original form.

2. **Proactively suggest better approaches.** When you discover a more optimal path during execution — simpler architecture, cleaner pattern, more efficient algorithm — proactively suggest it to the user. Don't silently follow a suboptimal plan when you see a better one.

# Work Habits

1. **Summarize corrections to memory.** When corrected by the user, summarize the reason and lesson learned, then write it to memory. This prevents repeating the same mistake in future sessions.

2. **Maintain existing code style.** When modifying existing code, match the surrounding style — naming conventions, formatting, patterns, comment style. Even if you'd write it differently in a new file, consistency matters more than personal preference.

# Boundaries

1. **Never auto-push code.** Do not push commits to remote unless the user explicitly asks. Local commits are fine; pushing requires explicit instruction.

## MCP 工具权限配置

使用 ReqFlow MCP 工具前，需要配置 Claude Code 的工具权限，避免每次调用都弹出确认提示：

```bash
# 运行安装脚本（推荐）
bash scripts/setup_mcp_permissions.sh
```

或手动添加到 `~/.claude/settings.local.json`：

```json
{
  "permissions": {
    "allow": [
      "mcp__reqflow__*"
    ]
  }
}
```

配置后重启 Claude Code 生效。`mcp__reqflow__*` 通配符允许所有 reqflow MCP 工具自动执行，无需逐个确认。
