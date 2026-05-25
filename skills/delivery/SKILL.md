---
name: delivery
description: >
  ⛔ 必须在对话中输出详细阶段报告、置信度评估、Agent 共识。
  ⛔ 必须派遣指定 Agent，不得跳过。
  ⛔ 必须调用 reqflow_stage_report、reqflow_dispatch_agent。
  ⛔ 每阶段完成后必须等待用户确认，确认前不得进入下一阶段。
  交付验证、归档演进、API/UI/RPC 验证。
tools: [Bash, Read, Write, Edit, Glob, Grep, WebFetch]
execution_modes:
  lite:  # L0/L1
    agents: [test-gen-agent]
    workers: [build-agent]
    discussion_rounds: 1
  standard:  # L2
    agents: [test-gen-agent, doc-agent]
    workers: [build-agent, deploy-agent]
    discussion_rounds: 2
  full:  # L3
    agents: [test-gen-agent, doc-agent, security-agent]
    workers: [build-agent, deploy-agent, test-runner-agent]
    discussion_rounds: 2+
---

# delivery

交付验证阶段。API/UI/RPC 验证、归档演进。

## ⛔ 核心规则（必须遵循）

> **以下规则不可违反。违反任何一条即为流程失败。**

### 规则 1: 必须通过 MCP 工具启动

```
reqflow_plan(requirement="<需求描述>")
```

**不得自行编排流程，不得跳过 MCP 调用。**

### 规则 2: 必须执行所有阶段

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

### 规则 3: P0 阻塞时必须停止

遇到以下情况必须停止等待用户决策：
- 有 P0 级 BLOCKER
- 验证失败
- 归档不完整

### 规则 4: 必须等待用户验收

所有阶段完成后必须停止，等待用户调用 `reqflow_accept` 或 `reqflow_reject`。**不得自行调用 `reqflow_accept`。**

---

### ⛔ Agent 确认要求

使用 `reqflow_dispatch_agent` 派遣 Agent 后，⛔ **必须** 使用平台 subagent 能力实际派遣 Agent，然后调用 `reqflow_agent_confirm` 确认完成：

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

---

## ⛔ V7 强制规则

### 每阶段必须调用 `reqflow_stage_report`

每个阶段完成后，⛔ **必须** 调用 `reqflow_stage_report` 生成结构化报告。

### 每阶段必须派遣指定 Agent

| 阶段 | 必须派遣的 Agent |
|------|------------------|
| 交付验证 | test-gen-agent |
| 归档 | doc-agent |

派遣时必须调用 `reqflow_dispatch_agent`。

### 归档前必须检查产物完整性

归档阶段开始前，⛔ **必须** 调用 `reqflow_artifact_check` 检查产物完整性。

### 生成产物时必须注册

每次生成产物文件时，⛔ **必须** 调用 `reqflow_artifact_register` 注册。

---

## 执行逻辑

### 步骤 1: 派遣主 Agent

```
🧪 test-gen-agent: 验证测试
📝 doc-agent: 文档更新
🔒 security-agent: 安全验证
```

### 步骤 2: 派遣辅助 Worker

```
🔧 build-agent: 执行构建验证
🔧 deploy-agent: 执行部署验证
🔧 test-runner-agent: 运行测试套件
```

### 步骤 3: 多轮讨论

- 第 1 轮：各 Agent 独立分析，输出初步结论
- 第 2 轮：交叉评审，识别分歧和共识
- 后续轮次：聚焦分歧，直到达成共识

### 步骤 4: 输出结论

汇总讨论结果，输出结构化报告。

---

## ⛔ MCP 工具与对话输出分离规则

**核心原则：MCP 返回的 `display` 字段包含格式化内容，必须在对话中展示给用户。**

### 对话输出模板

**调用 `reqflow_stage_report` 后必须输出：**

```
### 📋 阶段报告：交付验证

**状态:** ✅ 完成 | ⚠️ 有警告 | ❌ 失败

#### 产出清单
| 文件 | 操作 | 存在 | 状态 |
|------|------|------|------|
| test-report.md | 新增 | ✅ | 通过 |
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
| test-gen-agent | ... | 86% |
| doc-agent | ... | 92% |

#### MCP 执行追踪
| 工具 | 参数 | 结果 |
|------|------|------|
| reqflow_report | stage="交付验证" | ✅ |
| reqflow_stage_report | stage_name="交付验证" | ✅ |
| reqflow_dispatch_agent | agent="test-gen-agent" | ✅ |

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

### 验收决策面板

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

### MCP 即时反馈

每次调用 MCP 工具后，必须在对话中输出一行反馈：

```
📡 reqflow_report(stage="交付验证") → ✅ 已记录 (阶段 9/11, 81%)
```

⛔ **禁止静默调用 MCP 工具不输出。**

---

## 产物验证

每个修改文件的阶段结束后，必须验证产物：
- 调用 ArtifactVerifier 检查文件是否存在
- 输出产物验证表

---

## 相关 Skills

- `execution` — Agent 执行阶段
- `delivery-check` — 独立交付验证（可单独使用）
- `ship` — 独立发布流程（可单独使用）
- `write-docs` — 独立文档撰写（可单独使用）

## 强制规则

- **必须执行所有阶段，不得跳过**
- **必须等待用户验收，不得自行结束**
- **每阶段必须执行自检和问题发现**
- **每阶段必须在对话中展示产出摘要，不能只写到文件里**
- **每阶段完成后必须等待用户确认，确认前不得进入下一阶段**
- **不得静默调用 MCP 工具 — 每次调用后必须输出 📡 即时反馈**
- **多 Agent 协作必须真实派遣（平台有 subagent 就用），不得自扮多角色**
- **每个阶段必须输出完整阶段报告（含确认面板）**
- **每个阶段必须验证产物文件存在性**
- **所有阶段完成后必须展示验收决策面板（4 选项）**
