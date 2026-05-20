---
name: requirement-flow
description: >
  ReqFlow 主入口。接收需求、PRD、issue、bug、重构请求，自动路由到合适的执行级别。
  Harness 模式：生成 Execution Skill，Agent 按剧本执行。
  V4: 全流程自检纠错、辅助 Agent 集成、多方案对比、关键模块确认。
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

ReqFlow 根据需求内容自动路由到不同级别，每个级别映射到 YAML 管线的不同阶段子集：

### L0 - 只读分析（5 阶段）
- 只检查，不修改
- 启动 → PRD理解 → 上下文发现 → 分析报告 → 归档

### L1 - 轻量修改（6 阶段）
- 单文件、低风险
- 启动 → PRD理解 → 上下文发现 → 轻量实现 → 局部验证 → 归档

### L2 - 计划性修改（9 阶段）
- 多文件功能开发
- 启动 → PRD理解 → 上下文发现 → 技术方案 → 实施计划 → Agent执行 → 代码审查 → 交付验证 → 归档

### L3 - 交付循环（11 阶段）
- API/DB/消息/安全/部署相关变更
- 启动 → PRD理解 → Spec治理 → 工作流智能 → 上下文发现 → 技术方案 → 实施计划 → Agent执行 → 代码审查 → 交付验证 → 归档

## V4 全流程自检纠错

每个阶段（除启动和归档）执行时，遵循标准动作序列：

```
自检 → 问题发现 → 自行修复 → 辅助 Agent → 确认点
```

- **自检**：检查本阶段产出的完整性和一致性
- **问题发现**：主动识别潜在问题、遗漏、矛盾
- **自行修复**：小问题直接修复，记录到报告
- **辅助 Agent**：按需调用专项 Agent（research, architecture, security, performance, test-gen, debug, doc）
- **确认点**：向用户展示结果，等待确认

**技术方案阶段必须对比 2-3 个候选方案，给出推荐。关键模块完成后必须暂停等待用户确认。**

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

### 规则 5: 用户拒绝后必须进入修复循环
**⛔ 这是一个循环，不是单次操作。Agent 不得在拒绝后结束会话。**

`reqflow_reject` → 询问具体原因 → 回到相关阶段修复 → 重新走完后续阶段 → 重新门禁验证 → 再次展示结果 → 再次等待用户验收 → 如果再次拒绝 → 继续循环

**循环无次数上限 — 必须持续直到用户调用 `reqflow_accept`。**

**处理完用户任何反馈后，必须主动回到验收流程：**
- 用户说"测试一下" → 执行测试 → 测试通过后**必须主动重新提交验收**
- 用户说"改一下XX" → 修改 → 修改完成后**必须主动重新提交验收**
- 用户给出任何反馈 → 处理完成后**必须主动询问是否通过验收**
- **不能等用户再次触发验收，必须主动发起**

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
- **每阶段必须执行自检和问题发现**
- **技术方案必须对比 2-3 个候选方案**
- **关键模块完成后必须等待用户确认**
- **小问题自行修复但必须在报告中列出**
- **辅助 Agent 的 findings 必须纳入最终报告**

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
