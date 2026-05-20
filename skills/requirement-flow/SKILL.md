---
name: requirement-flow
description: >
  ReqFlow 主入口。接收需求、PRD、issue、bug、重构请求，自动路由到合适的执行级别。
  Harness 模式：生成 Execution Skill，Agent 按剧本执行。
  V3: 支持 3 种入口点、BLOCKER 管理、上下文保护、模块循环。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
---

# requirement-flow

ReqFlow Harness 主入口 skill。接收用户需求，自动路由并生成 Execution Skill。

## 核心理念

**Harness 生成剧本，Agent 执行演出。**

ReqFlow 不直接调用模型，而是：
1. 分析需求，决定路由级别
2. 扫描项目上下文
3. 生成 Execution Skill（执行剧本）
4. Agent 按剧本执行，通过 MCP 工具回报状态

## 触发方式

**Claude Code:**
```
/reqflow:requirement-flow <需求描述>
```

**Codex / Copilot / Cursor (通过 MCP):**
```
reqflow_plan(requirement="<需求描述>")
```

**自然语言触发:**
- "分析一下这个需求"
- "帮我实现这个功能"
- "做个修改计划再动手"
- "跑完整流程"
- "修个 bug"

## 入口点

| 入口点 | 触发方式 | 起始阶段 |
|--------|----------|----------|
| prd | 默认，从 PRD/需求开始 | PRD 理解 |
| tech_plan | 传入技术方案内容 | 代码梳理 |
| resume | 传入已有 run_id | 根据 state.json |

## 路由级别

### L0 - 只读分析
- 只检查，不修改
- 输出分析结果和建议

### L1 - 轻量修改
- 单文件、低风险
- 直接实现 + 局部检查

### L2 - 计划性修改
- 多文件功能开发
- 先出计划 → 确认 → 实现 → 验证

### L3 - 交付循环
- API/DB/消息/安全相关变更
- 计划 → 实现 → 构建 → 部署 → 验证 → 修复循环

## 执行流程

### 步骤 1: 创建计划
调用 `reqflow_plan` 开始新计划：
```
reqflow_plan(requirement="添加用户分页查询功能")
```

Harness 会：
- 路由分析（L0/L1/L2/L3）
- 入口点检测（prd/tech_plan/resume）
- 上下文扫描
- 生成 Execution Skill
- 返回计划摘要和 Execution Skill 路径

### 步骤 2: 读取 Execution Skill
```
cat .dev-workflow/runs/<run-id>/exec-skill.md
```

### 步骤 3: 按阶段执行
按 Execution Skill 定义的阶段顺序执行：
1. 上下文理解
2. 设计
3. 实现计划
4. 实现
5. 代码审查
6. 交付验证
7. 归档

每个阶段完成后调用 `reqflow_report` 报告状态。

### 步骤 4: BLOCKER 管理
使用 `reqflow_blocker_add` 和 `reqflow_blocker_resolve` 管理 BLOCKER：
- P0 必须全部关闭才能进入下一阶段
- P1 记录但不阻塞
- P2 仅记录

### 步骤 5: 门禁检查
需要门禁检查时调用 `reqflow_verify`：
```
reqflow_verify(run_id="<run-id>", gate="design-gate", evidence={...})
```

### 步骤 6: 用户验收
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
| `reqflow_acceptance_update` | 更新验收标准状态 |

## 相关 Skills

- `harness-orchestrator` — 如何使用 Execution Skill
- `context-understanding` — 上下文理解方法
- `design-phase` — 设计阶段方法
- `quality-gates` — 质量门禁说明
- `loop-repair` — 循环修复说明

## 强制规则

- 先路由，再执行
- L2/L3 必须先展示计划并获得确认
- 外部写操作必须等待确认
- 同一失败指纹出现两次时停止自动重试
- 秘钥不得写入项目文件
- P0 BLOCKER 必须全部关闭才能进入下一阶段
- 不要在受保护分支上直接提交

## 输出格式

```
REQUIREMENT_FLOW_STATUS: analyzed|implemented|delivered|blocked
ROUTE_LEVEL: L0|L1|L2|L3
ENTRY_POINT: prd|tech_plan|resume
SUMMARY:
- <简明结果>
NEXT_ACTION:
- <用户需要的下一步操作>
```
