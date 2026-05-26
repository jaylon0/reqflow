---
name: main-flow
description: >
  ⛔ 必须在对话中输出详细阶段报告、置信度评估、Agent 共识。
  ⛔ 必须派遣指定 Agent，不得跳过。
  ⛔ 必须调用 reqflow_stage_report、reqflow_dispatch_agent。
  ⛔ 每阶段完成后必须等待用户确认，确认前不得进入下一阶段。
  完整 PRD-to-code 流程。10 阶段管线，支持 checkpoint 恢复、loop 修复循环。
---

# main-flow

完整 PRD-to-code 交付流程，10 阶段管线。

## ⛔ 核心规则（必须遵循）

> **以下规则不可违反。违反任何一条即为流程失败。**

### 规则 1: 必须通过 MCP 工具启动

```
reqflow_full_flow(requirement="<需求描述>")
```

**不得自行编排流程，不得跳过 MCP 调用。**

### 规则 2: 必须读取 Execution Skill

启动后读取生成的 Execution Skill，确认路由级别和阶段列表。**不得修改 Execution Skill 本身。**

### 规则 3: 必须执行所有阶段

**每个阶段必须完整执行以下全部动作，不得跳过、不得简化、不得合并：**

```
┌─────────────────────────────────────────────────────────────┐
│  ① 执行阶段任务                                              │
│     ↓                                                       │
│  ② 自检（产出完整性、一致性、遗漏）                           │
│     ↓                                                       │
│  ③ 问题发现（主动识别问题，小问题自行修复）                    │
│     ↓                                                       │
│  ④ ⛔ 强制 Agent 视角输出（多 Agent 协作）                    │
│     ↓                                                       │
│  ⑤ ⛔ 共识表（必须输出）                                     │
│     ↓                                                       │
│  ⑥ ⛔ 质量门（必须执行）                                     │
│     ↓                                                       │
│  ⑦ ⛔ 置信度评估（6 维度）                                   │
│     ↓                                                       │
│  ⑧ ⛔ 反思点（必须执行）                                     │
│     ↓                                                       │
│  ⑨ 产物验证（文件存在性检查）                                 │
│     ↓                                                       │
│  ⑩ ⛔ 在对话中展示产出摘要（不是只写文件）                    │
│     ↓                                                       │
│  ⑪ ⛔ 调用 reqflow_stage_report 报告阶段状态                 │
│     ↓                                                       │
│  ⑫ ⛔ 停止等待用户确认（不得自动进入下一阶段）                 │
└─────────────────────────────────────────────────────────────┘
```

### 规则 4: 不得跳过任何阶段

按 Execution Skill 定义的阶段顺序执行，**不得跳过任何阶段**。

### 规则 5: P0 阻塞时必须停止

遇到以下情况必须停止等待用户决策：
- 有 P0 级 BLOCKER
- spec delta 变更持久行为
- 场景检测有歧义
- 关键模块完成（数据库 schema、核心业务逻辑、安全代码、多服务接口）

### 规则 6: 必须等待用户验收

所有阶段完成后必须停止，等待用户调用 `reqflow_accept` 或 `reqflow_reject`。**不得自行调用 `reqflow_accept`。**

---

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

派遣时必须调用 `reqflow_dispatch_agent` 注册意图：

```
reqflow_dispatch_agent(
    run_id="<run_id>",
    stage_name="<阶段名称>",
    agent_role="research-agent",
    task_description="任务描述"
)
```

⛔ **必须** 使用平台 subagent 能力实际派遣 Agent，然后调用 `reqflow_agent_confirm` 确认完成：

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

**阶段报告会自动检查讨论轮次，不足 2 轮时返回警告。**

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

辅助 Skill 通过 `/skill-name` 斜杠命令或自然语言触发调用。

### ⛔ Skill 调用追踪要求

每次调用 Skill（无论是宿主 Agent 还是 subagent），⛔ **必须** 调用 `reqflow_skill_invoke` 记录：

```
reqflow_skill_invoke(
    run_id="<run_id>",
    stage="<阶段名称>",
    skill_name="<Skill 名称>",
    invoked_by="host",  # host 或 subagent
    agent_role="",  # 如果是 subagent 调用，填写 agent 角色
    context="为什么调用这个 Skill",
    result_summary="Skill 执行结果摘要"
)
```

**追踪要求：**
1. **宿主 Agent 调用 Skill** — 必须记录，invoked_by="host"
2. **Subagent 调用 Skill** — 必须记录，invoked_by="subagent"，agent_role="对应角色"
3. **Skill 调用日志** — 在对话中输出详细的 Skill 调用过程和结果

**示例：**
```
📚 reqflow_skill_invoke(skill_name="prd-review", invoked_by="host")
   → Skill 调用已记录：prd-review (由宿主 Agent 在 PRD理解 阶段调用)
   → 宿主 Agent 必须在对话中描述：为什么调用、执行过程、关键发现
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
    → 返回 debate_id, 角色分配, host_instruction
    ↓
② ⛔ 并行派遣所有 Agent 独立分析（使用 Agent tool 并行调用）
    收集各方结论后调用 reqflow_debate_round 记录第一轮
    ↓
③ ⛔ 并行派遣所有 Agent 进行交叉评论
    每个 Agent 的 prompt 必须包含其他 Agent 的结论
    每个 Agent 必须回应其他 Agent 的结论
    收集后调用 reqflow_debate_round 记录新一轮
    ↓
④ 重复③直到 is_stable=true 或达到 max_rounds
    ↓
⑤ reqflow_debate_conclude(debate_id="<debate_id>")
    → 返回共识结论, 加权投票结果
```

**⛔ 辩论轮次 opinions 格式（必须包含交叉评论）：**

```python
reqflow_debate_round(
    debate_id="<debate_id>",
    round=1,
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
        },
        {
            "role": "pessimist",
            "agent": "architecture-agent",
            "conclusion": "我的结论...",
            "confidence": 0.78,
            "reasoning": "推理过程...",
            "cross_commentary": {
                "optimist": "我对乐观派结论的看法...",
                "pragmatist": "我对务实派结论的看法..."
            }
        }
    ]
)
```

**⛔ 辩论输出要求：**

宿主 Agent 必须在对话中用自己的语言描述：
1. 各 Agent 的核心观点和分歧点
2. 交叉评论中的关键交锋
3. 观点演变过程
4. 最终共识如何达成

**不得只展示 MCP 返回值。**

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

## 产物验证

每个修改文件的阶段结束后，必须验证产物：
- 调用 ArtifactVerifier 检查文件是否存在
- 输出产物验证表：
  ```
  #### 产物验证
  | 文件 | 操作 | 存在 | 状态 |
  |------|------|------|------|
  | PlaceholderController.java | 修改 | ✅ | 通过 |
  产物完整性: 1/1 通过
  ```

---

## ⛔ 验收决策面板

所有阶段完成后必须展示完整验收决策面板：

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

---

## 10 阶段

0. 启动/恢复运行 — 初始化 state.json
1. PRD 理解 — 提取功能点、约束、验收标准
2. Spec Governance — spec 变更合规检查
3. Workflow Intelligence — 场景检测、画像、工作项分解
4. Java Context Discovery — 代码图、语义索引、影响分析
5. Technical Plan — 架构选型、接口设计、数据模型
6. Implementation Plan — 模块拆分、依赖排序、上下文包
7. Agent Execution — 调度 dev/verify/review Agent，修复循环
8. Code Review — 质量门禁、编码规范检查
9. Delivery Verification — API/UI/RPC 验证
10. Archive and Evolution — 归档、演进建议

## Graph 编排模式

main-flow 支持 Graph YAML 定义，替代线性 stages：

```yaml
graph:
  entry: "analyze"
  nodes:
    - id: "analyze"
      type: "agent"
    - id: "gate"
      type: "decision"
    - id: "implement"
      type: "agent"
    - id: "verify"
      type: "agent"
  edges:
    - source: "analyze"
      target: "gate"
    - source: "gate"
      target: "implement"
      condition: "confidence >= 0.7"
    - source: "gate"
      target: "clarify"
      condition: "confidence < 0.7"
    - source: "clarify"
      target: "implement"
    - source: "implement"
      target: "verify"
```

## Loop 修复循环

Stage 9 验证失败时进入 loop engine：
```
observe → classify → localize → patch → verify → review → decide
```
最多 3 轮，相同失败指纹则停止。

## Checkpoint 恢复

每个 checkpoint 阶段会保存 state.json。中断后可从断点恢复：
```python
engine = Engine(config=config, run_dir="<之前的run-dir>")
# 自动从上次 checkpoint 继续
```

## Session 跨轮次

使用 Session 保存跨轮次上下文：
```python
session = Session(session_id="main-flow-run-1", storage_dir=".reqflow/sessions")
session.save_context("prd_summary", "...")
session.add_history("stage_1", "PRD 分析完成")
session.save()
```

## ⛔ MCP 工具与对话输出分离规则

**核心原则：MCP 返回的 `display` 只包含状态信息，详细内容由宿主 Agent 在对话中生成。**

### 强制约束

1. **MCP 返回的 `host_instruction` 字段必须遵循** — 每个 MCP 工具返回的 JSON 中包含 `host_instruction` 字段，明确指示宿主 Agent 必须执行的操作
2. **宿主 Agent 必须产出真实输出** — 不得直接展示 MCP 返回值，必须用自己的语言详细描述：
   - Agent 的工作过程和结论
   - 讨论的交锋过程
   - 置信度的含义和风险
   - 下一步行动建议
3. **使用 Agent 昵称** — MCP 返回的 `agent_nickname` 和 `agent_display_name` 字段提供友好昵称（如"小研"、"架构师"），在对话中必须使用昵称而非原始 agent_role
4. **MCP 返回值中的 `output_required: true`** — 表示 agent 必须在对话中输出内容

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

## 禁止事项

- **不得自行编排流程 — 必须通过 MCP 工具启动**
- **不得跳过任何阶段**
- **不得跳过自检和问题发现**
- **不得跳过 Agent 视角输出 — 必须通过 Agent tool 真实派遣**
- **不得跳过共识表**
- **不得跳过质量门**
- **不得跳过置信度评估（6 维度）**
- **不得跳过反思点**
- **不得跳过产物验证**
- **不得跳过在对话中展示摘要**
- **不得跳过 reqflow_report 调用**
- **不得在有 P0 阻塞时继续执行**
- **不得自行调用 reqflow_accept**
- **不得静默调用 MCP 工具 — 每次调用后必须输出 📡 即时反馈**
- **技术方案不得只给一个方案 — 必须对比 2-3 个候选方案**
- **不得跳过 reqflow_stage_report 调用 — 每阶段必须生成结构化报告**
- **不得跳过 reqflow_dispatch_agent 调用 — 派遣 Agent 时必须记录**
- **不得跳过 reqflow_acceptance_options 调用 — 验收时必须生成选项**
- **不得跳过 reqflow_artifact_register 调用 — 生成产物时必须注册**
- **不得跳过 reqflow_artifact_check 调用 — 归档前必须检查完整性**
- **不得跳过关键阶段的结构化辩论 — PRD理解/技术方案/代码审查/交付验证必须启动辩论**
- **不得跳过 reqflow_debate 调用 — 辩论启动时必须记录**
- **不得跳过 reqflow_debate_round 调用 — 每轮辩论必须记录**
- **不得跳过 reqflow_debate_conclude 调用 — 辩论结束时必须总结**
- **不得跳过交叉验证 — 关键决策必须使用 reqflow_cross_validate**

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
