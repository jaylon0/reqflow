---
name: requirement-flow
description: >
  ⛔ 必须在对话中输出详细阶段报告、置信度评估、Agent 共识。
  ⛔ 必须派遣指定 Agent，不得跳过。
  ⛔ 必须调用 reqflow_stage_report、reqflow_dispatch_agent。
  ⛔ 每阶段完成后必须等待用户确认，确认前不得进入下一阶段。
  ReqFlow 主入口。接收需求、PRD、issue、bug、重构请求，自动路由到合适的执行级别。
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

## 全流程入口

**强制 L3 全流程：**
- Slash: `/reqflow:full-flow <需求>`
- 自然语言: "跑完整流程" / "完整执行"
- MCP: `reqflow_full_flow(requirement="...")`

**指定级别：**
- MCP: `reqflow_plan(requirement="...", level="L2")`

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
执行任务 → 自检 → 问题发现 → 自行修复 → 辅助 Agent → 对话中展示摘要 → 等待确认
```

- **自检**：检查本阶段产出的完整性和一致性
- **问题发现**：主动识别潜在问题、遗漏、矛盾
- **自行修复**：小问题直接修复，在对话中列出
- **辅助 Agent**：按需调用专项 Agent，在对话中展示 findings 摘要
- **对话中展示摘要**：每个阶段必须在对话中给出概括，不能只写到文件里
- **确认点**：展示结果后 ⛔ 停止执行，等待用户确认后才进入下一阶段

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

## ⛔ MCP 即时输出规则

每次调用 MCP 工具后，必须立即在对话中输出：

1. **工具名 + 输入参数摘要**（一行，📡 前缀）
2. **返回结果摘要**（一行，用 ✅/❌ 标记）
3. **失败时输出失败原因和修复计划**

格式：
```
📡 reqflow_report(stage="PRD理解") → ✅ 已记录 (阶段 2/11, 18%)
📡 reqflow_verify(gate="tdd-gate") → ❌ 未通过: failing_tests_count 缺失
🔧 修复计划: 编写失败测试后重新提交
```

⛔ **禁止静默调用 MCP 工具不输出。**

## ⛔ Agent 真实派遣规则

**核心原则：多 Agent 协作必须真实派遣独立执行单元，不得自己扮演多个角色。**

### 平台检测与适配

执行前必须检测当前平台的多 Agent 能力，按以下优先级使用：

| 平台 | 派遣方式 | 并行 | 说明 |
|------|----------|------|------|
| Claude Code | Agent tool (subagent) | ✅ | `.claude/agents/` 定义，同一消息多 Agent tool call 并行；实验性 Agent Teams 支持多实例协作 |
| Codex | Subagent workflows | ✅ | `.codex/agents/` TOML 定义，默认 max_threads=6，内置 default/worker/explorer，`/agent` 管理线程 |
| Cursor | Cloud agents | ✅ | Agents Window 管理，支持 fleets of parallelized agents，Jira 集成触发，automations 定时触发 |
| GitHub Copilot | Coding Agent | 有限 | VS Code agent mode + 自主 PR 创建，CLI 层面无 subagent |
| Gemini CLI | **无 subagent** | ❌ | 单 agent + MCP 工具扩展，无多 agent 能力 |
| 其他平台 | 检测可用能力 | ? | 有 subagent 就用，没有则记录限制 |

**检测规则：**
1. 检查当前工具是否支持 subagent / 子 agent / 多 agent 派遣
2. 如果支持 → **必须使用真实派遣**，不得跳过
3. 如果不支持（如 Gemini CLI）→ 记录 `[限制] 当前平台不支持多 Agent 派遣，使用单 Agent 顺序执行`，在对话中明确告知用户

### 派遣规范

每个阶段的 agent 角色矩阵由 Execution Skill 定义。派遣时：
- 同一阶段的 agents 必须**并行派遣**（平台支持时）或**顺序派遣**（平台不支持并行时）
- 每个 agent 的 prompt 必须包含：**角色定义、任务描述、上下文、输出格式**
- 主 agent 不得"代替"任何子 agent 回答
- 子 agent 超时或失败时，按降级策略处理
- **无论使用何种平台，都不得跳过多 Agent 协作步骤 — 即使需要手动顺序执行每个角色的分析，也必须分别输出各角色的独立结论**

## ⛔ V7 强制规则

### 每阶段必须调用 `reqflow_stage_report`

每个阶段完成后，⛔ **必须** 调用 `reqflow_stage_report` 生成结构化报告：

```
reqflow_stage_report(
    run_id="<run_id>",
    stage_name="<阶段名称>",
    completed_items=["完成项1", "完成项2"],
    risk_items=["风险项1"],
    confidence_score=85,
    next_steps=["下一步1"],
    artifacts=["产物1.md"]
)
```

### 每阶段必须派遣指定 Agent

根据阶段自动派遣指定 Agent，不得跳过：

| 阶段 | 必须派遣的 Agent |
|------|------------------|
| 启动 | 无 |
| PRD理解 | research-agent, architecture-agent |
| Spec治理 | security-agent |
| 工作流智能 | research-agent |
| 上下文发现 | research-agent |
| 技术方案 | architecture-agent, security-agent |
| 实施计划 | test-gen-agent |
| Agent执行 | 动态派遣 |
| 代码审查 | security-agent, performance-agent |
| 交付验证 | test-gen-agent |
| 总结 | doc-agent |
| 归档 | 无 |

派遣时必须调用 `reqflow_dispatch_agent`：

```
reqflow_dispatch_agent(
    run_id="<run_id>",
    stage_name="<阶段名称>",
    agent_role="research-agent",
    task_description="任务描述"
)
```

### 验收时必须调用 `reqflow_acceptance_options`

交付验证阶段完成后，⛔ **必须** 调用 `reqflow_acceptance_options` 生成验收选项：

```
reqflow_acceptance_options(
    run_id="<run_id>",
    deliverables=["交付物1", "交付物2"],
    verification_results=[
        {"item": "编译", "status": "pass", "detail": "BUILD SUCCESS"},
        {"item": "测试", "status": "pass", "detail": "1 test passed"}
    ]
)
```

### 生成产物时必须注册

每次生成产物文件时，⛔ **必须** 调用 `reqflow_artifact_register` 注册：

```
reqflow_artifact_register(
    run_id="<run_id>",
    stage="<阶段名称>",
    artifacts=["文件路径1", "文件路径2"]
)
```

### 归档前必须检查产物完整性

归档阶段开始前，⛔ **必须** 调用 `reqflow_artifact_check` 检查产物完整性：

```
reqflow_artifact_check(run_id="<run_id>")
```

如果有缺失产物，必须补齐后才能继续。

---

## ⛔ 阶段报告结构

每个阶段完成后必须在对话中输出完整报告：

```
### 📋 阶段报告：{stage_name}

**状态:** ✅ 完成 | ⚠️ 有警告 | ❌ 失败

#### 产出清单
| 文件 | 操作 | 存在 | 状态 |
|------|------|------|------|
| xxx.java | 新增 | ✅ | 通过 |
产物完整性: 1/1 通过

#### 置信度（6 维度 + Unicode 可视化）
| 维度 | 分数 | 进度 | 热力 | 趋势 |
|------|------|------|------|------|
| 完整性 | 0.85 | ████████░ | 🟩 | ↑ |
| 一致性 | 0.90 | █████████ | 🟩 | → |
| 准确性 | 0.78 | ███████░░ | 🟨 | ↑ |
| 可测试性 | 0.72 | ███████░░ | 🟨 | → |
| 风险覆盖 | 0.65 | ██████░░░ | 🟧 | ↓ |
| Spec合规 | 0.80 | ████████░ | 🟩 | ↑ |
**综合: 0.79 (medium)**

#### Agent 共识
| Agent | 结论 | 置信度 |
|-------|------|--------|
| leader-agent | ... | 86% |
| dev-agent | ... | 92% |

#### MCP 执行追踪
| 工具 | 参数 | 结果 |
|------|------|------|
| reqflow_report | stage="PRD理解" | ✅ |

#### 问题与风险
- [自修复] xxx
- [需确认] xxx
- [阻塞] xxx

#### 趋势
置信度趋势: 0.72 → 0.79 (↑0.07)

#### 下一步
...

#### 阶段确认面板

### 📋 阶段确认：{stage_name}
| 选项 | 操作 | 说明 |
|------|------|------|
| ✅ 确认通过 | 进入下一阶段 | 产出已验证 |
| 🔄 重新执行 | 重新运行本阶段 | 发现问题 |
| ✏️ 修改需求 | 调整需求后重新分析 | 需求变化 |
| ⏭ 跳过 | 直接进入下一阶段 | 不推荐 |
```

## ⛔ 阶段确认面板

每个阶段结束时必须展示确认选项：

```
### 📋 阶段确认：{stage_name}
| 选项 | 操作 | 说明 |
|------|------|------|
| ✅ 确认通过 | 进入下一阶段 | 产出已验证 |
| 🔄 重新执行 | 重新运行本阶段 | 发现问题 |
| ✏️ 修改需求 | 调整需求后重新分析 | 需求变化 |
| ⏭ 跳过 | 直接进入下一阶段 | 不推荐 |
```

## ⛔ 验收决策面板

所有阶段完成后必须展示完整验收决策面板：

```
### 🏁 验收决策面板
**当前状态:** 全部阶段完成，等待你的验收决定。
#### 已交付产物清单
#### 质量摘要
#### 请做出决定
| 选项 | 操作 | 后续流程 |
|------|------|----------|
| ✅ 通过验收 | reqflow_accept | 归档、清理、流程结束 |
| ❌ 拒绝验收 | reqflow_reject | 修复循环（最多 3 轮） |
| 🔧 部分验收 | reqflow_accept + scope | 部分归档 |
| ⏸ 暂挂 | 不调用工具 | 保持状态 |
```

## 产物验证

每个修改文件的阶段结束后，必须验证产物：
- 调用 ArtifactVerifier 检查文件是否存在
- 输出产物验证表

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

| 工具 | 用途 | 必须调用 |
|------|------|----------|
| `reqflow_plan` | 开始新计划 | - |
| `reqflow_run` | 执行 workflow | - |
| `reqflow_status` | 查询运行状态 | - |
| `reqflow_report` | 报告阶段完成 | ✅ 每阶段 |
| `reqflow_verify` | 门禁验证 | ✅ 有门禁时 |
| `reqflow_accept` | 用户验收通过 | - |
| `reqflow_reject` | 用户验收拒绝 | - |
| `reqflow_dashboard` | Dashboard 可视化 | - |
| `reqflow_blocker_add` | 添加 BLOCKER | - |
| `reqflow_blocker_resolve` | 解决 BLOCKER | - |
| `reqflow_blocker_check` | 检查 BLOCKER 状态 | - |
| `reqflow_memory_save` | 保存长期记忆 | - |
| `reqflow_memory_load` | 加载长期记忆 | - |
| `reqflow_git_check` | 检查 Git 状态 | - |
| `reqflow_acceptance_update` | 更新验收标准状态 | - |
| `reqflow_health` | 健康检查 | - |
| `reqflow_stage_report` | 生成结构化阶段报告 | ✅ 每阶段 |
| `reqflow_dispatch_agent` | 记录并验证 Agent 派遣 | ✅ 派遣时 |
| `reqflow_acceptance_options` | 生成验收选项 | ✅ 验收时 |
| `reqflow_artifact_register` | 注册生成的产物 | ✅ 生成产物时 |
| `reqflow_artifact_check` | 检查产物完整性 | ✅ 归档前 |

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
- **每阶段必须在对话中展示产出摘要，不能只写到文件里**
- **每阶段完成后必须等待用户确认，确认前不得进入下一阶段**
- **技术方案必须对比 2-3 个候选方案**
- **关键模块完成后必须等待用户确认**
- **小问题自行修复但必须在对话中列出**
- **辅助 Agent 的 findings 必须在对话中展示摘要**
- **不得静默调用 MCP 工具 — 每次调用后必须输出 📡 即时反馈**
- **多 Agent 协作必须真实派遣（平台有 subagent 就用），不得自扮多角色**
- **每个阶段必须输出完整阶段报告（含确认面板）**
- **每个阶段必须验证产物文件存在性**
- **所有阶段完成后必须展示验收决策面板（4 选项）**

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
