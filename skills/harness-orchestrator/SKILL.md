---
name: harness-orchestrator
description: >
  Harness 编排器 — 告诉 Agent 如何读取和执行 Execution Skill。
  这是 ReqFlow 的核心编排模式：Harness 生成剧本，Agent 执行演出。
  V3: 集成 BLOCKER 管理、上下文保护、模块循环、长期记忆、Git 工作流。
---

# Harness 编排器

你是 ReqFlow Harness 的执行者。Harness 已经为你生成了一个 Execution Skill（执行剧本），
你的任务是按照剧本执行。

## ⛔ 强制执行协议

> **以下规则不可违反。违反任何一条即为流程失败。**

### 1. 必须执行所有阶段

读取 Execution Skill 后，**必须按顺序执行其中定义的每一个阶段**。
- 不得跳过任何阶段
- 不得提前结束
- 不得在只完成部分阶段时声称"已完成"

### 2. 每阶段必须报告

每个阶段完成后，**必须调用 `reqflow_report`**：
```
reqflow_report(run_id="<run-id>", stage="<阶段名称>", status="done", artifacts=[...])
```

### 3. 门禁必须验证

Execution Skill 中指定的门禁，**必须调用 `reqflow_verify`** 验证。
门禁未通过 → 修复 → 重新验证。不得跳过。

### 4. 必须等待用户验收

所有阶段完成后，**必须停止并等待用户验收**：
- 展示完成状态和产出物摘要
- 告知用户："所有阶段已完成，请验收。`reqflow_accept` 通过 / `reqflow_reject` 拒绝。"
- **不得自行调用 `reqflow_accept`**
- **不得在未收到用户验收决定前结束会话**

### 5. 用户拒绝后必须进入修复循环

**⛔ 这是一个循环，不是单次操作。Agent 不得在拒绝后结束会话。**

```
用户调用 reqflow_reject
        │
        ▼
  记录拒绝原因
        │
        ▼
  用户未提供具体原因？
    ┌───┴───┐
    │ 是    │ 否
    ▼       ▼
  询问用户  分析问题
  具体哪里  确定修复范围
  不满意
    │       │
    └───┬───┘
        ▼
  回到相关阶段修复
  (代码→Agent执行, 设计→技术方案, 验证→交付验证)
        │
        ▼
  重新走完后续所有阶段
        │
        ▼
  重新调用 completion-gate
        │
        ▼
  再次展示完成状态
        │
        ▼
  再次等待用户验收 ←──┐
        │              │
        ▼              │
  用户调用 accept?     │
    ┌───┴───┐          │
    │ 是    │ 否       │
    ▼       ▼          │
  流程结束  再次 reject ┘
```

**循环无次数上限 — 必须持续直到用户调用 reqflow_accept。**

### 修复循环中的关键行为规则

**处理完用户任何反馈后，Agent 必须主动回到验收流程：**

- 用户说"测试一下" → 执行测试 → 测试通过后**必须主动重新提交验收**
- 用户说"改一下XX" → 修改 → 修改完成后**必须主动重新提交验收**
- 用户给出任何反馈 → 处理完成后**必须主动询问是否通过验收**
- **不能等用户再次触发验收，必须主动发起**

## 入口点

Execution Skill 头部定义了入口点（entry_point）：

| 入口点 | 说明 | 起始阶段 |
|--------|------|----------|
| prd | 从 PRD 开始完整流程 | PRD 理解 / 上下文理解 |
| tech_plan | 从技术方案开始 | 代码梳理 |
| resume | 从断点恢复 | 根据 state.json |

## 路由级别

Execution Skill 头部定义了路由级别（routing_level），决定阶段模板：

| 级别 | 阶段数 | 阶段 |
|------|--------|------|
| L0 | 5 | 启动 → PRD理解 → 上下文发现 → 分析报告 → 归档 |
| L1 | 6 | 启动 → PRD理解 → 上下文发现 → 轻量实现 → 局部验证 → 归档 |
| L2 | 9 | 启动 → PRD理解 → 上下文发现 → 技术方案 → 实施计划 → Agent执行 → 代码审查 → 交付验证 → 归档 |
| L3 | 11 | 启动 → PRD理解 → Spec治理 → 工作流智能 → 上下文发现 → 技术方案 → 实施计划 → Agent执行 → 代码审查 → 交付验证 → 归档 |

**Agent 必须按 Execution Skill 中定义的阶段顺序执行。**

## BLOCKER 管理

每个阶段可能产生 BLOCKER，按严重程度分级：

| 级别 | 含义 | 处理方式 |
|------|------|----------|
| P0 | 阻塞，必须关闭 | 所有 P0 关闭前不得进入下一阶段 |
| P1 | 标记，不阻塞 | 记录并在后续阶段处理 |
| P2 | 仅记录 | 仅记录，不影响流程 |

使用 `reqflow_blocker_add` 添加 BLOCKER，`reqflow_blocker_resolve` 解决。

## 上下文保护

为防止上下文溢出：

1. **搜索结果限制** — 每次搜索最多返回 50 条结果
2. **子代理隔离** — IO 密集型任务使用子代理执行
3. **阶段清理** — 每个阶段结束时清理临时文件

## Subagent 协调（Agent 执行阶段）

Agent 执行阶段使用多智能体协调模式：

```
┌─────────────┐
│  dev-agent   │  ← 实现代码
└──────┬───────┘
       │ 成功后并行调度
  ┌────┴────┐
  ▼         ▼
┌────────┐ ┌────────┐
│verify- │ │review- │  ← 并行验证+审查
│agent   │ │agent   │
└────────┘ └────────┘
```

- **dev-agent**: 负责代码实现（acceptEdits 权限）
- **verify-agent**: 负责构建和测试验证（auto 权限，与 review 并行）
- **review-agent**: 负责代码质量和 spec 合规审查（plan 权限，与 verify 并行）

**模型选择策略：**
- opus: 数据库 schema 变更、多服务协调、安全敏感代码、>5 验收标准
- sonnet: 标准 API 变更、简单业务逻辑、测试补充、<=5 验收标准

## 模块级 8 步循环

每个模块按 8 步循环执行：

```
prepare → build → generate → self_check → review → confirm → commit → update_state
```

使用 `reqflow_report` 报告每个步骤的状态。

## Loop Engine（修复循环）

失败时进入修复循环状态机：

```
observe → classify → localize → patch → verify → review → decide
```

- **observe**: 收集失败信息（构建错误、测试失败、审查发现）
- **classify**: 分类失败原因（code_issue/test_issue/environment_issue/requirement_unclear）
- **localize**: 定位问题文件和代码位置
- **patch**: 生成修复补丁
- **verify**: 运行测试验证修复
- **review**: 审查修复是否引入新问题
- **decide**: 决定是否继续循环或升级

**风险门禁（触发升级到用户）：**
- 同一问题指纹出现两次
- 最大重试次数达到（3 轮）
- 修复需要修改授权模块外的文件
- 需求或预期行为不明确
- 外部依赖不可用

## 长期记忆

使用 `reqflow_memory_save` 和 `reqflow_memory_load` 管理跨会话记忆：

- **decision** — 架构决策、技术选型
- **constraint** — 约束条件、限制
- **naming** — 命名规则、约定
- **pattern** — 代码模式、最佳实践

## Git 工作流

使用 `reqflow_git_check` 检查分支状态：

- 自动检测受保护分支（master, main, develop, release）
- BLOCKER 修复使用独立提交
- 小步提交，每个逻辑变更一个提交

## 执行流畅性

**减少用户中断，只在关键决策点暂停：**

| 操作类型 | 处理方式 |
|----------|----------|
| MCP reqflow_* 工具调用 | 自动执行，不弹确认 |
| 文件读写、编辑 | 自动执行，不弹确认 |
| 测试运行、构建命令 | 自动执行，不弹确认 |
| Git commit（小步提交） | 自动执行，不弹确认 |
| Spec 治理（持久行为变更） | **暂停等待用户确认** |
| 技术方案（架构/接口/数据决策） | **暂停等待用户确认** |
| 人工确认点（模块完成确认） | **暂停等待用户确认** |
| 验收决定 | **暂停等待用户决定** |

**前提条件：** 需要配置 MCP 工具权限（`~/.claude/settings.local.json` 中添加 `mcp__reqflow__*`），详见 `scripts/setup_mcp_permissions.sh`。

## 禁止事项

- 不要跳过任何阶段
- 不要跳过质量门禁
- 不要在没有验证证据的情况下声称完成
- 不要修改 Execution Skill 本身（它是 Harness 生成的）
- 不要忽略 BLOCKED 状态
- 不要在受保护分支上直接提交
- 不要忽略 P0 BLOCKER
- **不要自行调用 `reqflow_accept` — 只有用户才能验收**
- **不要在未收到用户验收决定前结束会话**
- **不要在用户拒绝验收后结束会话 — 必须进入修复循环**

## 执行流程

```
1. 读取 Execution Skill
2. 理解全局约束和路由级别
3. 检查入口点（prd/tech_plan/resume）
4. 按阶段顺序执行（必须执行所有阶段）:
   a. 执行阶段任务
   b. 管理 BLOCKER（P0 必须关闭）
   c. 调用 reqflow_report 报告状态
   d. 如果有门禁，调用 reqflow_verify
   e. 如果门禁未通过，按指引修复
5. 所有阶段完成后，调用 reqflow_dashboard 展示面板
6. 汇总产出物，告知用户等待验收
7. 【强制停止】等待用户调用 reqflow_accept 或 reqflow_reject
8. 如果用户拒绝 → 回到步骤 4 修复
9. 如果用户通过 → 流程结束
```

## 状态报告格式

每个阶段完成后，调用：
```
reqflow_report(
    run_id="<run-id>",
    stage="<阶段名称>",
    status="done",  # done | blocked | timeout | failed
    artifacts=["<产出文件路径>"],
)
```

## 门禁检查格式

需要门禁检查时，调用：
```
reqflow_verify(
    run_id="<run-id>",
    gate="completion-gate",  # design-gate | tdd-gate | completion-gate | compliance-report
    evidence={...},
)
```

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
