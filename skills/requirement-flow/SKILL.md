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
1. 分析需求，决定路由级别（L0/L1/L2/L3）
2. 扫描项目上下文
3. 根据路由级别生成对应的 Execution Skill（执行剧本）
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
| prd | 默认，从 PRD/需求开始 | PRD 理解 / 上下文理解 |
| tech_plan | 传入技术方案内容 | 代码梳理 |
| resume | 传入已有 run_id | 根据 state.json |

## 路由级别

ReqFlow 根据需求内容自动路由到不同级别：

### L0 - 只读分析
- 只检查，不修改
- 阶段：上下文理解 → 分析报告

### L1 - 轻量修改
- 单文件、低风险
- 阶段：上下文理解 → 轻量实现 → 局部验证

### L2 - 计划性修改
- 多文件功能开发
- 阶段：上下文理解 → 技术方案 → 实施计划 → 生成代码 → 跨模块终检 → 总结

### L3 - 交付循环
- API/DB/消息/安全/部署相关变更
- 阶段：PRD理解 → 代码梳理 → 技术方案 → 实施计划 → 生成代码 → 跨模块终检 → 总结

## ⛔ 强制执行协议

> **以下规则不可违反。**

### 规则 1: 必须执行所有阶段
读取 Execution Skill 后，**必须按顺序执行每一个阶段**。不得跳过，不得提前结束。

### 规则 2: 每阶段必须报告
每个阶段完成后，**必须调用 `reqflow_report`**。

### 规则 3: 门禁必须验证
指定的门禁检查点，**必须调用 `reqflow_verify`**。未通过则修复后重新验证。

### 规则 4: 必须等待用户验收
所有阶段完成后，**必须停止并等待用户验收**。不得自行调用 `reqflow_accept`。

### 规则 5: 用户拒绝后必须修复
`reqflow_reject` → 修复 → 重新走完 → 再次等待验收。

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
- 根据路由级别生成 Execution Skill
- 返回计划摘要和 Execution Skill 路径

### 步骤 2: 读取 Execution Skill
```
cat .reqflow/runs/<run-id>/exec-skill.md
```

Execution Skill 头部包含路由级别和阶段列表。

### 步骤 3: 按阶段执行（强制所有阶段）
按 Execution Skill 定义的阶段顺序执行。每个阶段完成后调用 `reqflow_report` 报告状态。

### 步骤 4: BLOCKER 管理
使用 `reqflow_blocker_add` 和 `reqflow_blocker_resolve` 管理 BLOCKER：
- P0 必须全部关闭才能进入下一阶段
- P1 记录但不阻塞
- P2 仅记录

### 步骤 5: 门禁检查
需要门禁检查时调用 `reqflow_verify`：
```
reqflow_verify(run_id="<run-id>", gate="completion-gate", evidence={...})
```

### 步骤 6: 用户验收（强制停止点）
> **⛔ 所有阶段完成后，Agent 必须在此停止。**

展示完成状态，告知用户等待验收：
- 用户通过: `reqflow_accept(run_id="<run-id>")`
- 用户拒绝: `reqflow_reject(run_id="<run-id>", reason="...")`

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

## 相关 Skills

- `harness-orchestrator` — 如何使用 Execution Skill

## 强制规则

- 先路由，再执行
- L2/L3 必须先展示计划并获得确认
- 外部写操作必须等待确认
- 同一失败指纹出现两次时停止自动重试
- 秘钥不得写入项目文件
- P0 BLOCKER 必须全部关闭才能进入下一阶段
- 不要在受保护分支上直接提交
- **必须执行所有阶段，不得跳过**
- **必须等待用户验收，不得自行结束**

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
