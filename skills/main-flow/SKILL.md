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

每轮讨论必须调用 `reqflow_discussion_round` 记录：

```
reqflow_discussion_round(
    run_id="<run_id>",
    stage="<阶段名称>",
    round=1,
    agents=["agent1", "agent2"]
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

**核心原则：MCP 返回的 `display` 字段包含格式化内容，必须在对话中展示给用户。**

### 强制约束

1. **MCP 返回的 `display` 字段必须在对话中展示** — `reqflow_stage_report`、`reqflow_dispatch_agent`、`reqflow_acceptance_options` 等工具返回的 JSON 中包含 `display` 字段（含 `title` 和 `content`），Agent 必须将 `display.content` 的内容在对话中输出
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
```

⛔ **禁止静默调用 MCP 工具不输出。**

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

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
