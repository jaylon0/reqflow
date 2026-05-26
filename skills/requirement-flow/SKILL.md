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
每个阶段完成后，**必须先在对话中生成完整分析，再调用 `reqflow_stage_report` 验证**。如果返回 rejected，补充后重新调用。

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
| `reqflow_skill_invoke` | 记录 Skill 调用 | ✅ 调用 Skill 时 |

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
    conclusion="Subagent 的实际结论内容（至少 50 字）"
)
```

⛔ conclusion 必须是非空的真实结论，MCP 会验证内容长度。

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

### ⛔ 关键阶段结构化辩论要求（真实多 Agent 交互）

以下关键阶段必须启动 **结构化辩论**，通过真实多 Agent 交互提高决策质量：

| 关键阶段 | 辩论角色 | 最少轮次 |
|----------|----------|----------|
| PRD理解 | 乐观派 + 悲观派 + 务实派 | 2 轮 |
| 技术方案 | 乐观派 + 悲观派 + 务实派 + 批评者 | 2 轮 |
| 代码审查 | 悲观派 + 批评者 | 2 轮 |
| 交付验证 | 悲观派 + 批评者 + 务实派 | 2 轮 |

**真实辩论流程（必须并行派遣）：**

```
① reqflow_debate(stage="技术方案", topic="架构选型")
    → 返回 debate_id, 角色列表
    ↓
② ⛔ 并行派遣所有 Agent 独立分析（使用 Agent tool 并行调用）
    收集各方结论后，在对话中描述各方观点
    调用 reqflow_debate_round 记录第一轮（必须包含 host_debate_analysis）
    ↓
③ ⛔ 并行派遣所有 Agent 进行交叉评论
    每个 Agent 的 prompt 必须包含其他 Agent 的结论
    每个 Agent 必须回应其他 Agent 的结论
    收集后，在对话中描述交锋过程
    调用 reqflow_debate_round 记录新一轮
    ↓
④ 重复③直到 is_stable=true 或达到 max_rounds
    ↓
⑤ 在对话中描述辩论过程和最终共识
    调用 reqflow_debate_conclude（必须包含 final_consensus，至少 100 字）
```

**⛔ 辩论轮次调用格式（必须包含 host_debate_analysis 和 cross_commentary）：**

```python
reqflow_debate_round(
    debate_id="<debate_id>",
    round=1,
    host_debate_analysis="你在对话中生成的辩论分析（至少 100 字）",
    opinions=[
        {
            "role": "optimist",
            "agent": "research-agent",
            "conclusion": "我的结论...",
            "confidence": 0.85,
            "reasoning": "推理过程...",
            "cross_commentary": {
                "pessimist": "我对悲观派结论的看法...",
                "pragmatist": "我对务实派结论的看法..."
            }
        }
    ]
)
```

⛔ **如果 MCP 返回 rejected，说明你的分析不达标，补充后重新调用。**

### ⛔ Skill 强制调用规则

**以下阶段必须调用对应 Skill，否则 `reqflow_stage_report` 会返回 rejected：**

| 阶段 | 必须调用（否则 rejected） | 可选调用 |
|------|---------------------------|----------|
| PRD理解 | `/prd-review` | - |
| 技术方案 | `/tech-plan`, `/security-audit` | `/impact-analysis` |
| 代码审查 | `/code-review`, `/security-audit` | `/vuln-scan`, `/code-quality`, `/adversarial-review` |
| 交付验证 | `/delivery-check` | `/test-gen`, `/test-coverage` |
| 总结 | `/write-docs` | `/retro` |

**调用流程：**
1. 在对话中执行阶段任务
2. 调用对应的 Skill（如 `/prd-review`）
3. Skill 执行完成后，调用 `reqflow_skill_invoke(result_summary="至少 30 字的结果摘要")` 记录
4. 然后调用 `reqflow_stage_report` 验证

⛔ **不得跳过 required Skill 调用。MCP 工具会检查 Skill 调用记录，未调用则 rejected。**
⛔ **result_summary 必须至少 30 字，不得写占位符。**

## ⛔ MCP 工具验证架构

**核心原则：MCP 工具是验证者，不是内容生成者。你必须先在对话中生成完整内容，再调 MCP 验证。**

### 强制约束

1. **先生成，再验证** — 每个 MCP 工具调用前，你必须先在对话中生成完整分析
2. **rejected 必须修复** — 如果 MCP 返回 `status: "rejected"`，根据 `missing` 字段补充后重新调用
3. **不得展示 MCP 返回值** — MCP 返回只有状态信息（status/stage/progress），没有可展示内容
4. **使用 Agent 昵称** — 在对话中使用"小研"、"架构师"等昵称，不用原始 agent_role

### MCP 即时反馈

每次调用 MCP 工具后，必须在对话中输出一行反馈：

```
📡 reqflow_report(stage="PRD理解") → ✅ 已记录 (阶段 2/11, 18%)
📡 reqflow_dispatch_agent(stage="PRD理解", agent="research-agent") → ✅ 小研已注册
📡 reqflow_agent_confirm(dispatch_id="xxx") → ✅ 小研已完成
📡 reqflow_stage_report(stage="PRD理解") → 🟨 置信度 82/100
📡 reqflow_debate(stage="技术方案", topic="架构选型") → 🎭 辩论启动 (4 角色)
📡 reqflow_debate_round(debate_id="xxx", round=1) → 🔄 未稳定，3 个观点
📡 reqflow_debate_conclude(debate_id="xxx") → 🏛️ 共识度 85%
```

⛔ **禁止静默调用 MCP 工具不输出。**

### ⛔ 对话输出要求

每次 MCP 调用后，宿主 Agent 必须在对话中用自己的语言产出详细分析，包括但不限于：

1. **Agent 派遣后** — 说明为什么派遣、Agent 的任务、预期产出
2. **Agent 确认后** — 用自己的语言描述 Agent 的工作过程和结论
3. **阶段报告后** — 分析置信度含义、风险、下一步行动
4. **辩论轮次后** — 描述各方观点的交锋和分歧点
5. **辩论结束后** — 总结辩论过程、共识达成原因、保留异议价值

**不得只展示 MCP 返回的 JSON。**

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
