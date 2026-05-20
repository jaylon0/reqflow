---
name: using-reqflow
description: >
  ReqFlow Harness 使用指南。从需求到交付的完整工程化流程。
  Harness 模式：生成 Execution Skill，Agent 按剧本执行。
  V3: 集成 BLOCKER 管理、上下文保护、模块循环、长期记忆、Git 工作流。
---

# using-reqflow

ReqFlow Harness 使用指南。引导用户完成从需求到交付的全流程。

## 核心理念

**Harness 生成剧本，Agent 执行演出。**

ReqFlow 是一个 Harness（编排器），它：
1. 分析需求，决定路由级别（L0/L1/L2/L3）
2. 扫描项目上下文
3. 根据路由级别生成对应的 Execution Skill（执行剧本）
4. Agent 按剧本执行，通过 MCP 工具回报状态

## 触发方式

**自然语言：**
```
使用 reqflow 帮我处理这个需求：<需求内容>
```

**Slash 命令：**
```
/reqflow:using-reqflow <需求内容>
```

## 路由级别与阶段模板

ReqFlow 根据需求内容自动路由到不同级别，每个级别映射到 YAML 管线的不同阶段子集：

| 级别 | 触发条件 | 阶段数 | 阶段 |
|------|----------|--------|------|
| L0 只读分析 | 分析/评估/解释类请求 | 5 | 启动 → PRD理解 → 上下文发现 → 分析报告 → 归档 |
| L1 轻量修改 | 单文件低风险修复 | 6 | 启动 → PRD理解 → 上下文发现 → 轻量实现 → 局部验证 → 归档 |
| L2 计划性修改 | 多文件功能开发 | 9 | 启动 → PRD理解 → 上下文发现 → 技术方案 → 实施计划 → Agent执行 → 代码审查 → 交付验证 → 归档 |
| L3 交付循环 | API/DB/消息/安全/部署变更 | 11 | 启动 → PRD理解 → Spec治理 → 工作流智能 → 上下文发现 → 技术方案 → 实施计划 → Agent执行 → 代码审查 → 交付验证 → 归档 |

**Agent 必须按 Execution Skill 中定义的阶段顺序执行，不得跳过任何阶段。**

## 强制执行协议

> **⛔ 以下规则不可违反，违反任何一条即为流程失败。**

### 规则 1: 必须执行所有阶段

Agent 读取 Execution Skill 后，**必须按顺序执行其中定义的每一个阶段**。
不得跳过任何阶段，不得提前结束，不得在只完成部分阶段时声称"已完成"。

### 规则 2: 每阶段必须报告

每个阶段完成后，**必须调用 `reqflow_report`** 报告该阶段状态：
```
reqflow_report(run_id="<run-id>", stage="<阶段名称>", status="done", artifacts=[...])
```

### 规则 3: 门禁必须验证

Execution Skill 中指定的门禁检查点，**必须调用 `reqflow_verify`** 进行验证：
- L2/L3 的"跨模块终检"阶段必须调用 `reqflow_verify(gate="completion-gate")`
- L0/L1 的"局部验证"/"分析报告"阶段根据 Execution Skill 指引决定是否需要门禁
- 门禁未通过时，必须按指引修复后重新验证，不得跳过

### 规则 4: 必须等待用户验收

所有阶段完成后，Agent **必须停止执行并等待用户验收**：
- 向用户展示完成状态和产出物摘要
- **明确告知用户**："所有阶段已完成，请验收。调用 `reqflow_accept` 通过或 `reqflow_reject` 拒绝。"
- **不得自行调用 `reqflow_accept`** — 只有用户才能决定是否通过
- **不得在未收到用户验收决定前结束会话**

### 规则 5: 用户拒绝后必须进入修复循环

**⛔ 这是一个循环，不是单次操作。Agent 不得在拒绝后结束会话。**

如果用户调用 `reqflow_reject`，Agent 必须：
1. 记录拒绝原因（如果用户未提供具体原因，主动询问）
2. 回到相关阶段修复问题（代码→Agent执行, 设计→技术方案, 验证→交付验证）
3. 修复后重新走完剩余阶段
4. 重新调用门禁验证
5. 再次展示完成状态
6. 再次等待用户验收
7. 如果再次拒绝 → 继续循环

**循环无次数上限 — 必须持续直到用户调用 `reqflow_accept`。**

**处理完用户任何反馈后，必须主动回到验收流程：**
- 用户说"测试一下" → 执行测试 → 测试通过后**必须主动重新提交验收**
- 用户说"改一下XX" → 修改 → 修改完成后**必须主动重新提交验收**
- 用户给出任何反馈 → 处理完成后**必须主动询问是否通过验收**
- **不能等用户再次触发验收，必须主动发起**

## 流程

### 1. 创建计划

调用 `reqflow_plan` 开始新计划：
```
reqflow_plan(requirement="<需求描述>")
```

Harness 会自动：
- 路由分析（L0/L1/L2/L3）
- 入口点检测（prd/tech_plan/resume）
- 上下文扫描（项目结构、技术栈、入口文件）
- 根据路由级别生成对应的 Execution Skill

### 2. 读取 Execution Skill

```
cat .reqflow/runs/<run-id>/exec-skill.md
```

Execution Skill 头部包含路由级别和阶段列表，Agent 必须据此执行。

### 3. 按阶段执行（强制）

按 Execution Skill 定义的阶段**顺序执行**。每个阶段完成后必须调用 `reqflow_report`。

### 4. BLOCKER 管理

每个阶段可能产生 BLOCKER：

| 级别 | 含义 | 处理方式 |
|------|------|----------|
| P0 | 阻塞，必须关闭 | 所有 P0 关闭前不得进入下一阶段 |
| P1 | 标记，不阻塞 | 记录并在后续阶段处理 |
| P2 | 仅记录 | 仅记录，不影响流程 |

使用 `reqflow_blocker_add` 添加，`reqflow_blocker_resolve` 解决。

### 5. 门禁检查

需要门禁检查时调用 `reqflow_verify`：
```
reqflow_verify(run_id="<run-id>", gate="completion-gate", evidence={...})
```

### 6. 用户验收（强制停止点）

> **⛔ 所有阶段完成后，Agent 必须在此停止。**

Agent 必须：
1. 调用 `reqflow_dashboard` 展示运行面板
2. 汇总所有已完成阶段和产出物
3. 告知用户："请验收。通过请调用 `reqflow_accept`，拒绝请调用 `reqflow_reject`。"
4. **等待用户响应，不得自行结束**

### 7. 验收结果处理

- 用户通过: `reqflow_accept(run_id="<run-id>")`
- 用户拒绝: `reqflow_reject(run_id="<run-id>", reason="...")`

拒绝后 Agent 回到修复流程，修复完成后再次等待验收。

## MCP 工具

| 工具 | 用途 |
|------|------|
| `reqflow_plan` | 开始新计划 |
| `reqflow_run` | 执行 workflow |
| `reqflow_status` | 查询运行状态 |
| `reqflow_report` | 报告阶段完成 |
| `reqflow_verify` | 门禁验证 |
| `reqflow_accept` | 用户验收通过 |
| `reqflow_reject` | 用户验收拒绝 |
| `reqflow_dashboard` | Dashboard 可视化 |
| `reqflow_blocker_add` | 添加 BLOCKER |
| `reqflow_blocker_resolve` | 解决 BLOCKER |
| `reqflow_blocker_check` | 检查 BLOCKER 状态 |
| `reqflow_memory_save` | 保存长期记忆 |
| `reqflow_memory_load` | 加载长期记忆 |
| `reqflow_git_check` | 检查 Git 状态 |
| `reqflow_acceptance_update` | 更新验收标准状态 |
| `reqflow_health` | 健康检查 |

## 相关 Skills

- `requirement-flow` — 主入口
- `harness-orchestrator` — 如何使用 Execution Skill
