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

## 核心规则

1. **读取 Execution Skill** — 它在 `.dev-workflow/runs/<run-id>/exec-skill.md`
2. **按阶段执行** — 不要跳过阶段，不要提前执行
3. **报告状态** — 每个阶段完成后调用 `reqflow_report`
4. **请求验证** — 门禁检查时调用 `reqflow_verify`
5. **等待指引** — 遇到 BLOCKED 时调用 `reqflow_status` 获取下一步

## 入口点

Execution Skill 头部定义了入口点（entry_point）：

| 入口点 | 说明 | 起始阶段 |
|--------|------|----------|
| prd | 从 PRD 开始完整流程 | PRD 理解 |
| tech_plan | 从技术方案开始 | 代码梳理 |
| resume | 从断点恢复 | 根据 state.json |

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

## 模块循环

每个模块按 8 步循环执行：

```
prepare → build → generate → self_check → review → confirm → commit → update_state
```

使用 `reqflow_report` 报告每个步骤的状态。

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

## 外部工具

使用 `reqflow_tool_call` 调用外部工具（通过 MCP 协议）：

- docs-shuttle — 文档管理
- common-components — 公共组件查询
- coding-standards — 编码规范检查
- pitfall — 常见陷阱检查

## 自由发挥空间

Execution Skill 定义了"做什么"，但"怎么做"由你决定：
- 具体的代码实现方式
- 测试用例的选择
- 重构的方向
- 工具的使用方式

## 禁止事项

- 不要跳过质量门禁
- 不要在没有验证证据的情况下声称完成
- 不要修改 Execution Skill 本身（它是 Harness 生成的）
- 不要忽略 BLOCKED 状态
- 不要在受保护分支上直接提交
- 不要忽略 P0 BLOCKER

## 执行流程

```
1. 读取 Execution Skill
2. 理解全局约束
3. 检查入口点（prd/tech_plan/resume）
4. 按阶段顺序执行:
   a. 执行阶段任务
   b. 管理 BLOCKER（P0 必须关闭）
   c. 调用 reqflow_report 报告状态
   d. 如果有门禁，调用 reqflow_verify
   e. 如果门禁未通过，按指引修复
5. 所有阶段完成后，等待用户验收
6. 用户验收通过后，调用 reqflow_accept
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
    gate="design-gate",  # design-gate | tdd-gate | completion-gate | compliance-report
    evidence={...},
)
```

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
