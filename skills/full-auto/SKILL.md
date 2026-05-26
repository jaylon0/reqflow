---
name: full-auto
description: >
  ⛔ 必须在对话中输出详细阶段报告、置信度评估、Agent 共识。
  ⛔ 必须派遣指定 Agent，不得跳过。
  ⛔ 必须调用 reqflow_stage_report、reqflow_dispatch_agent。
  ⛔ 必须调用 reqflow_acceptance_options 生成验收选项。
  全自动授权模式，阶段确认自动通过，仅在最终验收时停止。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
---

# full-auto

全自动授权模式。与标准 main-flow 完全一致，只是阶段确认自动通过。

## ⛔ 核心规则（必须遵循）

> **以下规则不可违反。违反任何一条即为流程失败。**

### 规则 1: 必须通过 MCP 工具启动

```
reqflow_full_flow(requirement="<需求描述>", auto_pilot=true)
```

**不得自行编排流程，不得跳过 MCP 调用，不得自行决定路由级别。即使需求很小，也必须通过 MCP 启动并执行完整 L3 流程。**

### 规则 2: 必须读取 Execution Skill

启动后读取生成的 Execution Skill，确认 `auto_pilot: true`。**不得修改 Execution Skill 本身。**

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
│  ⑨ 产物验证（文件存在性 + 内容质量检查）                      │
│     ↓                                                       │
│  ⑩ ⛔ 在对话中生成完整阶段分析（用自己的语言）                 │
│     ↓                                                       │
│  ⑪ ⛔ 调用 required Skill（如有）                            │
│     ↓                                                       │
│  ⑫ ⛔ 调用 reqflow_stage_report 验证你的分析                 │
│     ↓                                                       │
│  ⑬ 如果返回 rejected，补充缺失内容后重新调用                  │
│     ↓                                                       │
│  ⑭ 自动进入下一阶段（不等待用户确认）                         │
└─────────────────────────────────────────────────────────────┘
```

**与标准模式的唯一区别：⑭ 自动继续，而不是 ⛔ 停止等待用户确认。**
**⛔ MCP 工具是验证者，不是内容生成者。你必须先生成内容，再调 MCP 验证。**

### 规则 4: 不得跳过任何阶段

11 个阶段必须全部执行。**需求再小也必须走完 L3 全流程，不得因需求简单而缩减阶段。**

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

### 每阶段必须调用 `reqflow_stage_report`（验证模式）

每个阶段完成后，⛔ **必须** 先在对话中生成完整分析，再调用 `reqflow_stage_report` 验证：

```
reqflow_stage_report(
    run_id="<run_id>",
    stage_name="<阶段名称>",
    host_analysis="你在对话中生成的完整阶段分析（至少 100 字）",
    confidence_score=85,
    completed_items=["完成项1", "完成项2"],
    risk_items=["风险项1"],
    next_steps=["下一步1"],
    artifacts=["产物1.md"]
)
```

**⛔ 如果返回 `status: "rejected"`，根据 `missing` 字段补充后重新调用。**

### ⛔ Skill 强制调用规则

**以下阶段必须调用对应 Skill，否则 `reqflow_stage_report` 会返回 rejected：**

| 阶段 | 必须调用（否则 rejected） | 可选调用 |
|------|---------------------------|----------|
| PRD理解 | `/prd-review` | - |
| 技术方案 | `/tech-plan`, `/security-audit` | `/impact-analysis` |
| 代码审查 | `/code-review`, `/security-audit` | `/vuln-scan`, `/code-quality` |
| 交付验证 | `/delivery-check` | `/test-gen`, `/test-coverage` |
| 总结 | `/write-docs` | `/retro` |

调用后必须调用 `reqflow_skill_invoke(result_summary="至少 30 字的结果摘要")` 记录。

### 每阶段必须派遣指定 Agent

根据阶段自动派遣指定 Agent，不得跳过。派遣后调用 `reqflow_agent_confirm` 确认，conclusion 至少 50 字。

### 辩论要求

关键阶段辩论时，`reqflow_debate_round` 必须包含 `host_debate_analysis`（至少 100 字），`reqflow_debate_conclude` 必须包含 `final_consensus`（至少 100 字）。

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

### ⛔ 关键阶段必须启动结构化辩论（真实多 Agent 交互）

对于关键阶段（PRD理解、技术方案、代码审查、交付验证），⛔ **必须** 启动结构化辩论：

```
reqflow_debate(stage="技术方案", topic="架构选型")
```

**真实辩论流程（必须并行派遣）：**

```
① reqflow_debate → 返回 debate_id, 角色列表
② ⛔ 并行派遣所有 Agent 独立分析
③ 收集结论 → 在对话中描述各方观点 → reqflow_debate_round(round=1, host_debate_analysis="至少 100 字")
④ ⛔ 并行派遣所有 Agent 交叉评论（每个 Agent 必须回应其他 Agent 的结论）
⑤ 收集结论 → 在对话中描述交锋 → reqflow_debate_round(round=2, host_debate_analysis="至少 100 字")
⑥ 重复④⑤直到 is_stable=true 或达到 max_rounds
⑦ 在对话中描述辩论结论 → reqflow_debate_conclude(final_consensus="至少 100 字")
```

⛔ **如果 MCP 返回 rejected，补充分析后重新调用。**

**辩论角色分配：**

| 关键阶段 | 辩论角色 | 最少轮次 |
|----------|----------|----------|
| PRD理解 | 乐观派 + 悲观派 + 务实派 | 2 轮 |
| 技术方案 | 乐观派 + 悲观派 + 务实派 + 批评者 | 2 轮 |
| 代码审查 | 悲观派 + 批评者 | 2 轮 |
| 交付验证 | 悲观派 + 批评者 + 务实派 | 2 轮 |

**⛔ 辩论轮次 opinions 格式（必须包含 host_debate_analysis 和交叉评论）：**

```python
reqflow_debate_round(
    debate_id="<debate_id>",
    round=1,
    host_debate_analysis="你在对话中生成的辩论分析（至少 100 字，描述各方交锋）",
    opinions=[
        {
            "role": "optimist",
            "agent": "research-agent",
            "conclusion": "我的结论...",
            "confidence": 0.85,
            "reasoning": "推理过程...",
            "cross_commentary": {
                "pessimist": "我对悲观派结论的看法..."
            }
        }
    ]
)
```

### ⛔ Skill 调用追踪要求

每次调用 Skill，⛔ **必须** 调用 `reqflow_skill_invoke` 记录（result_summary 至少 30 字）。

---

## ⛔ MCP 工具验证架构

**核心原则：MCP 工具是验证者，不是内容生成者。你必须先在对话中生成完整内容，再调 MCP 验证。**

### 强制约束

1. **先生成，再验证** — 每个 MCP 工具调用前，你必须先在对话中生成完整分析
2. **rejected 必须修复** — 如果 MCP 返回 `status: "rejected"`，根据 `missing` 字段补充后重新调用
3. **不得展示 MCP 返回值** — MCP 返回只有状态信息，没有可展示内容
4. **使用 Agent 昵称** — 在对话中使用"小研"、"架构师"等昵称

### ⛔ 对话输出要求

每次 MCP 调用后，宿主 Agent 必须在对话中用自己的语言产出详细分析，包括但不限于：

1. **Agent 派遣后** — 说明为什么派遣、Agent 的任务、预期产出
2. **Agent 确认后** — 用自己的语言描述 Agent 的工作过程和结论
3. **阶段报告后** — 分析置信度含义、风险、下一步行动
4. **辩论轮次后** — 描述各方观点的交锋和分歧点
5. **辩论结束后** — 总结辩论过程、共识达成原因、保留异议价值

**不得只展示 MCP 返回的 JSON。**

---

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

### 禁止事项

- **不得自己扮演多个 Agent 角色** — 即使平台不支持 subagent，也必须分别以不同角色视角独立分析
- **不得跳过 Agent 视角输出** — 每个 required agent 都必须有独立结论
- **不得合并不同 Agent 的结论为单一输出**

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

#### 阶段确认面板（auto_pilot 自动选择第一选项但仍展示）

### 📋 阶段确认：{stage_name}
| 选项 | 操作 | 说明 |
|------|------|------|
| ✅ 确认通过 | 进入下一阶段 | 产出已验证 [自动选择] |
| 🔄 重新执行 | 重新运行本阶段 | 发现问题 |
| ✏️ 修改需求 | 调整需求后重新分析 | 需求变化 |
| ⏭ 跳过 | 直接进入下一阶段 | 不推荐 |
```

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

## 触发方式

**Slash 命令：**
```
/reqflow:full-auto <需求描述>
```

**自然语言：**
- "全自动授权执行：<需求>"
- "完全自动跑完整流程：<需求>"
- "full auto 执行：<需求>"

**MCP 直接调用：**
```
reqflow_full_flow(requirement="<需求描述>", auto_pilot=true)
```

---

## 与标准模式和其他入口的区别

| 维度 | /reqflow:main-flow | /reqflow:full-auto | /reqflow:auto-flow |
|------|-------------------|-------------------|-------------------|
| 阶段执行 | 全部 11 阶段 | 全部 11 阶段 | 全部 11 阶段 |
| 多 Agent 协作 | 有 | **有** | 无（跳过） |
| 共识表 | 有 | **有** | 无（跳过） |
| 质量门 | 有 | **有** | 无（跳过） |
| 置信度评估 | 有 | **有** | 无（跳过） |
| 反思点 | 有 | **有** | 无（跳过） |
| 中间确认 | ⛔ 停止 | 自动继续 | 自动继续 |
| P0 阻塞 | 停止 | 停止 | 停止 |
| 验收 | ⛔ 停止 | ⛔ 停止 | ⛔ 停止 |
| 适用场景 | 需要逐步确认 | 信任 Agent，要完整产出 | 快速测试 |

---

## 禁止事项

- **不得自行编排流程 — 必须通过 reqflow_full_flow(auto_pilot=true) 启动**
- **不得因需求简单而缩减阶段 — 必须执行全部 11 阶段**
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
