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
1. 分析需求，决定路由级别
2. 扫描项目上下文
3. 生成 Execution Skill（执行剧本）
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
- 生成 Execution Skill（执行剧本）

### 2. 读取 Execution Skill

```
cat .dev-workflow/runs/<run-id>/exec-skill.md
```

Execution Skill 定义了：
- 全局约束（BLOCKER 管理、上下文保护、Git 工作流）
- 入口点（prd/tech_plan/resume）
- 各阶段的具体任务
- MCP 工具使用指南
- 门禁检查点
- 暂停条件

### 3. 按阶段执行

按 Execution Skill 定义的阶段顺序执行：

| 阶段 | 任务 | 门禁 |
|------|------|------|
| 上下文理解 | 项目扫描、语义分析、完备性检查 | — |
| 设计 | Meta Spec、Feature Spec、技术方案 | design-gate |
| 实现计划 | 工作项分解、TDD 计划 | tdd-gate |
| 实现 | 编码、测试、重构 | — |
| 代码审查 | Spec 合规、代码质量 | completion-gate |
| 交付验证 | 构建、测试、合规报告 | compliance-report |
| 归档 | 用户验收、经验教训 | — |

每个阶段完成后调用 `reqflow_report` 报告状态。

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
reqflow_verify(run_id="<run-id>", gate="design-gate", evidence={...})
```

### 6. 长期记忆

使用 `reqflow_memory_save` 保存重要决策和约束：
```
reqflow_memory_save(
    category="decision",
    key="使用 PostgreSQL 而非 MySQL",
    content="因为需要 JSONB 支持",
    run_id="<run-id>"
)
```

使用 `reqflow_memory_load` 加载历史记忆。

### 7. 用户验收

完成所有阶段后，等待用户验收：
- 用户通过: `reqflow_accept(run_id="<run-id>")`
- 用户拒绝: `reqflow_reject(run_id="<run-id>", reason="...")`

## MCP 工具

| 工具 | 用途 |
|------|------|
| `reqflow_run` | 执行 workflow |
| `reqflow_status` | 查询运行状态 |
| `reqflow_list_runtimes` | 列出可用 runtime |
| `reqflow_run_graph` | 执行图编排 |
| `reqflow_session_save` | 保存会话 |
| `reqflow_session_load` | 加载会话 |
| `reqflow_dashboard` | Dashboard 可视化 |
| `reqflow_checkpoint` | 管理检查点 |
| `reqflow_parallel` | 并行 agent 调度 |
| `reqflow_trace` | 执行追踪 |
| `reqflow_guardrails` | 约束检查 |
| `reqflow_health` | 健康检查 |
| `reqflow_plan` | 开始新计划 |
| `reqflow_report` | 报告阶段完成 |
| `reqflow_verify` | 门禁验证 |
| `reqflow_accept` | 用户验收通过 |
| `reqflow_reject` | 用户验收拒绝 |
| `reqflow_tool_call` | 调用外部工具 |
| `reqflow_memory_save` | 保存长期记忆 |
| `reqflow_memory_load` | 加载长期记忆 |
| `reqflow_git_check` | 检查 Git 状态 |
| `reqflow_blocker_add` | 添加 BLOCKER |
| `reqflow_blocker_resolve` | 解决 BLOCKER |
| `reqflow_blocker_check` | 检查 BLOCKER 状态 |
| `reqflow_multi_repo_switch` | 多仓库切换 |

## 相关 Skills

- `requirement-flow` — 主入口
- `harness-orchestrator` — 如何使用 Execution Skill
- `context-understanding` — 上下文理解方法
- `design-phase` — 设计阶段方法
- `quality-gates` — 质量门禁说明
- `loop-repair` — 循环修复说明
