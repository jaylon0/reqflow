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

## ⛔ MCP 工具与对话输出分离规则

**核心原则：MCP 返回值是内部状态，不是给用户看的。Agent 必须在对话中生成完整报告。**

### 强制约束

1. **MCP 返回值不得直接展示** — `reqflow_stage_report`、`reqflow_dispatch_agent`、`reqflow_acceptance_options` 返回的是 JSON 状态，不是格式化报告
2. **Agent 必须在对话中生成报告** — 根据 MCP 输入参数和返回状态，在对话中输出完整的格式化报告
3. **MCP 返回值中的 `output_required: true`** — 表示 agent 必须在对话中输出内容

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

#### 问题与风险
- [自修复] xxx
- [需确认] xxx
- [阻塞] xxx

#### 趋势
置信度趋势: 0.72 → 0.79 (↑0.07)

#### 下一步
...
```

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
```

⛔ **禁止静默调用 MCP 工具不输出。**

---

## ⛔ Agent 真实派遣规则

**核心原则：多 Agent 协作必须真实派遣独立执行单元，不得自己扮演多个角色。**

### 平台检测与适配

执行前必须检测当前平台的多 Agent 能力，按以下优先级使用：

| 平台 | 派遣方式 | 并行 | 说明 |
|------|----------|------|------|
| Claude Code | Agent tool (subagent) | ✅ | `.claude/agents/` 定义，同一消息多 Agent tool call 并行 |
| Codex | Subagent workflows | ✅ | `.codex/agents/` TOML 定义，`/agent` 管理线程 |
| Cursor | Cloud agents | ✅ | Agents Window 管理，支持并行 agents |
| GitHub Copilot | Coding Agent | 有限 | VS Code agent mode + 自主 PR 创建 |
| Gemini CLI | **无 subagent** | ❌ | 单 agent + MCP 工具扩展 |
| 其他平台 | 检测可用能力 | ? | 有 subagent 就用，没有则记录限制 |

**检测规则：**
1. 检查当前工具是否支持 subagent / 子 agent / 多 agent 派遣
2. 如果支持 → **必须使用真实派遣**，不得跳过
3. 如果不支持（如 Gemini CLI）→ 记录 `[限制] 当前平台不支持多 Agent 派遣，使用单 Agent 顺序执行`

### 派遣规范

每个阶段的 agent 角色矩阵由 Execution Skill 定义。派遣时：
- 同一阶段的 agents 必须**并行派遣**（平台支持时）或**顺序派遣**（平台不支持并行时）
- 每个 agent 的 prompt 必须包含：**角色定义、任务描述、上下文、输出格式**
- 主 agent 不得"代替"任何子 agent 回答
- 子 agent 超时或失败时，按降级策略处理
- **无论使用何种平台，都不得跳过多 Agent 协作步骤**

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

#### 阶段确认面板

### 📋 阶段确认：{stage_name}
| 选项 | 操作 | 说明 |
|------|------|------|
| ✅ 确认通过 | 进入下一阶段 | 产出已验证 |
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

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
