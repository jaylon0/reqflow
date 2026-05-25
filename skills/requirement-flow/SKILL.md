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
| `reqflow_dispatch_agent` | 注册 Agent 派遣意图 | ✅ 派遣时 |
| `reqflow_agent_confirm` | 确认 Agent 实际派遣完成 | ✅ 派遣后 |
| `reqflow_discussion_round` | 记录讨论轮次 | ✅ 讨论时 |
| `reqflow_acceptance_options` | 生成验收选项 | ✅ 验收时 |
| `reqflow_artifact_register` | 注册生成的产物 | ✅ 生成产物时 |
| `reqflow_artifact_check` | 检查产物完整性 | ✅ 归档前 |
| `reqflow_debate` | 启动结构化辩论 | ✅ 关键阶段 |
| `reqflow_debate_round` | 记录辩论轮次 | ✅ 每轮辩论 |
| `reqflow_debate_conclude` | 总结辩论共识 | ✅ 辩论结束 |
| `reqflow_cross_validate` | 交叉验证 | ✅ 关键决策 |

### ⛔ Agent 派遣确认流程

派遣 Agent 时必须遵循两步流程：

1. 调用 `reqflow_dispatch_agent` 注册意图，获取 `dispatch_id`
2. 使用平台 subagent 能力实际派遣 Agent
3. 调用 `reqflow_agent_confirm` 确认完成

```
reqflow_agent_confirm(
    run_id="<run_id>",
    dispatch_id="<从 reqflow_dispatch_agent 返回>",
    status="completed",
    conclusion="Agent 结论摘要"
)
```

### ⛔ 关键阶段讨论轮次强制要求

以下关键阶段必须至少进行 **2 轮** Agent 讨论后才能提交阶段报告：

| 关键阶段 | 最少轮次 |
|----------|----------|
| PRD理解 | 2 轮 |
| 技术方案 | 2 轮 |
| 代码审查 | 2 轮 |
| 交付验证 | 2 轮 |

**讨论必须是真实的多 Agent 协作，不是简单的 MCP 调用标记。**

#### 真实讨论流程

```
① 观点陈述阶段 (phase="statements")
   - 派遣各 Agent 独立完成任务
   - 收集各方结论
   - 调用 reqflow_discussion_round 记录
     ↓
② 交叉评论阶段 (phase="cross_commentary")
   - 让每位 Agent 评论其他 Agent 的观点
   - 'A，你怎么看 B 的方案？B，你对 A 的担忧有何回应？'
   - 调用 reqflow_discussion_round 记录
     ↓
③ 共识达成
   - 分析共识点和分歧点
   - 调用 reqflow_consensus 记录最终共识
```

每轮讨论必须调用 `reqflow_discussion_round` 记录：

```
reqflow_discussion_round(
    run_id="<run_id>",
    stage="<阶段名称>",
    round=1,
    agents=["research-agent", "architecture-agent"],
    topic="讨论议题",
    phase="statements",  # statements / cross_commentary / full
    points=[
        {"agent": "research-agent", "point": "研究结论..."},
        {"agent": "architecture-agent", "point": "架构建议..."}
    ],
    cross_comments=[
        {"reviewer": "research-agent", "target": "architecture-agent", "comment": "对架构方案的看法..."}
    ],
    agreements=["共识1"],
    disagreements=["分歧1"],
    decision="最终决策"
)
```

### ⛔ 关键阶段结构化辩论要求

以下关键阶段必须启动 **结构化辩论**，通过角色化对抗讨论提高决策质量：

| 关键阶段 | 辩论角色 | 最少轮次 |
|----------|----------|----------|
| PRD理解 | 乐观派 + 悲观派 + 务实派 | 2 轮 |
| 技术方案 | 乐观派 + 悲观派 + 务实派 + 批评者 | 2 轮 |
| 代码审查 | 悲观派 + 批评者 | 2 轮 |
| 交付验证 | 悲观派 + 批评者 + 务实派 | 2 轮 |

**辩论流程：**

```
① reqflow_debate(stage="技术方案", topic="架构选型")
    → 返回 debate_id, 角色分配
    ↓
② 派遣 Agent 执行辩论（至少 2 轮）
    每轮调用 reqflow_debate_round 记录:
    reqflow_debate_round(
        debate_id="<debate_id>",
        round=1,
        arguments={"optimist": "...", "pessimist": "...", ...}
    )
    ↓
③ reqflow_debate_conclude(debate_id="<debate_id>")
    → 返回共识结论, 加权投票结果, 置信度
```

### 辅助 Skill 调用指引

根据阶段上下文，可调用相关辅助 Skill 增强能力：

| 阶段 | 推荐辅助 Skill | 调用时机 |
|------|----------------|----------|
| PRD理解 | `prd-review` | 审查 PRD 完整性 |
| 技术方案 | `tech-plan`, `security-audit`, `impact-analysis` | 方案设计、安全评估、影响分析 |
| 实施计划 | `test-gen` | 生成测试用例 |
| Agent执行 | `debug`, `refactor` | 调试问题、重构代码 |
| 代码审查 | `code-review`, `security-audit`, `vuln-scan`, `code-quality`, `adversarial-review` | 代码审查、安全扫描、质量检查、对抗性审查 |
| 交付验证 | `delivery-check`, `test-gen`, `test-coverage` | 交付验证、测试补充、覆盖率分析 |
| 总结 | `write-docs`, `retro` | 文档撰写、复盘分析 |

## ⛔ MCP 工具与对话输出分离规则

**核心原则：MCP 返回的数据是参考信息，宿主 Agent 必须用自己的语言产出详细的真实输出。**

### 强制约束

1. **MCP 返回的 `host_instruction` 字段必须遵循** — 每个 MCP 工具返回的 JSON 中包含 `host_instruction` 字段，明确指示宿主 Agent 必须执行的操作
2. **宿主 Agent 必须产出真实输出** — 不得直接展示 MCP 返回值，必须用自己的语言详细描述：
   - Agent 的工作过程和结论
   - 讨论的交锋过程
   - 置信度的含义和风险
   - 下一步行动建议
3. **使用 Agent 昵称** — MCP 返回的 `agent_nickname` 和 `agent_display_name` 字段提供友好昵称（如"小研"、"架构师"），在对话中必须使用昵称而非原始 agent_role
4. **MCP 返回值中的 `output_required: true`** — 表示 agent 必须在对话中输出内容

### 对话输出模板

**调用 `reqflow_stage_report` 后必须输出：**
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
| reqflow_stage_report | stage_name="PRD理解" | ✅ |
| reqflow_dispatch_agent | agent="research-agent" | ✅ |

#### 问题与风险
- [自修复] xxx（已自动修复）
- [需确认] xxx（需要用户确认）
- [阻塞] xxx（阻塞流程）

#### 反思点
- 本阶段决策: xxx
- 潜在改进: xxx
- 经验教训: xxx

#### 趋势
置信度趋势: 0.72 → 0.79 (↑0.07)

#### 下一步
...
```

**置信度可视化说明：**
- **进度条**: `████████░` 表示 80%，`█████░░░░` 表示 50%
- **热力图**: 🟩 (≥90%), 🟨 (≥70%), 🟧 (≥50%), 🟥 (<50%)
- **趋势箭头**: ↑ 提升, ↓ 下降, → 持平

**调用 `reqflow_dispatch_agent` 后必须输出：**
```
### 🤖 Agent 派遣：{agent_role}

**角色定义:**
- 名称: {name}
- 角色: {role}
- 能力: {capabilities}

**任务描述:**
{task_description}

**派遣指引:**
⛔ 必须使用平台的 subagent 能力派遣此 Agent：
- Claude Code: 使用 `Agent` tool
- Codex: 使用 subagent workflows
- Cursor: 使用 cloud agents

**Prompt 模板:**
```
{prompt_template}
```

**验证:**
- 当前阶段: {stage_name}
- 是否必须派遣: ✅ 是
- 还有未派遣的必须 Agent: {missing_agents}
```

**调用 `reqflow_acceptance_options` 后必须输出：**
```
### 🏁 验收决策面板

**当前状态:** 全部阶段完成，等待你的验收决定。

#### 已交付产物清单
| 文件 | 变更类型 | 验证状态 |
|------|----------|----------|
| xxx.java | 新增 | 编译通过 |

#### 质量摘要
- 门禁通过: 4/4
- 置信度: 0.79 (medium)
- P0 阻塞: 0
- 验收标准: 1/1 verified

#### 请做出决定
| 选项 | 操作 | 后续流程 |
|------|------|----------|
| ✅ 通过验收 | reqflow_accept | 归档、清理、流程结束 |
| ❌ 拒绝验收 | reqflow_reject | 修复循环（最多 3 轮） |
| 🔧 部分验收 | reqflow_accept + scope | 部分归档 |
| ⏸ 暂挂 | 不调用工具 | 保持状态 |
```

### MCP 即时反馈

每次调用 MCP 工具后，必须在对话中输出一行反馈：

```
📡 reqflow_report(stage="PRD理解") → ✅ 已记录 (阶段 2/11, 18%)
📡 reqflow_verify(gate="tdd-gate") → ❌ 未通过: failing_tests_count 缺失
🔧 修复计划: 编写失败测试后重新提交
📡 reqflow_debate(stage="技术方案", topic="架构选型") → 🎭 辩论启动 (4 角色)
📡 reqflow_debate_round(debate_id="xxx", round=1) → ✅ 第 1 轮记录
📡 reqflow_debate_conclude(debate_id="xxx") → ✅ 共识达成 (置信度: 85%)
📡 reqflow_cross_validate(task="xxx") → ✅ 交叉验证完成 (一致性: 0.92)
```

⛔ **禁止静默调用 MCP 工具不输出。**

---

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
- **不得跳过关键阶段的结构化辩论 — PRD理解/技术方案/代码审查/交付验证必须启动辩论**
- **不得跳过 reqflow_debate 调用 — 辩论启动时必须记录**
- **不得跳过 reqflow_debate_round 调用 — 每轮辩论必须记录**
- **不得跳过 reqflow_debate_conclude 调用 — 辩论结束时必须总结**
- **不得跳过交叉验证 — 关键决策必须使用 reqflow_cross_validate**

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
