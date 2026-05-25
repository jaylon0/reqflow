---
name: analysis
description: >
  ⛔ 必须在对话中输出详细阶段报告、置信度评估、Agent 共识。
  ⛔ 必须派遣指定 Agent，不得跳过。
  ⛔ 必须调用 reqflow_stage_report、reqflow_dispatch_agent。
  ⛔ 每阶段完成后必须等待用户确认，确认前不得进入下一阶段。
  需求分析、合规检查、场景检测、工作项分解。
tools: [Bash, Read, Write, Edit, Glob, Grep, WebFetch]
execution_modes:
  lite:  # L0/L1
    agents: [research-agent]
    workers: [code-search-agent]
    discussion_rounds: 1
  standard:  # L2
    agents: [research-agent, architecture-agent]
    workers: [code-search-agent, test-search-agent]
    discussion_rounds: 2
  full:  # L3
    agents: [research-agent, architecture-agent, security-agent]
    workers: [code-search-agent, test-search-agent, file-scanner-agent]
    discussion_rounds: 2+
---

# analysis

需求分析阶段。分析 PRD、提取功能点、检查合规、检测场景。

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
- spec delta 变更持久行为
- 场景检测有歧义

### 规则 4: 必须等待用户验收

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
| PRD理解 | research-agent, architecture-agent |
| Spec治理 | security-agent |
| 工作流智能 | research-agent |

派遣时必须调用 `reqflow_dispatch_agent`：

```
reqflow_dispatch_agent(
    run_id="<run_id>",
    stage_name="<阶段名称>",
    agent_role="research-agent",
    task_description="任务描述"
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

---

## 执行逻辑

### 步骤 1: 派遣主 Agent

根据 YAML 配置派遣主 Agent 进行讨论：

```
📋 research-agent: 调研需求背景、竞品方案
🏗️ architecture-agent: 分析现有架构、评估影响
🔒 security-agent: 评估安全风险、合规要求
```

### 步骤 2: 派遣辅助 Worker

并行派遣 Worker 收集信息：

```
🔧 code-search-agent: 搜索相关代码
🔧 test-search-agent: 搜索现有测试
```

### 步骤 3: 多轮讨论

Worker 结果传递给主 Agent，开始讨论：

- 第 1 轮：各 Agent 独立分析，输出初步结论
- 第 2 轮：交叉评审，识别分歧和共识
- 后续轮次：聚焦分歧，直到达成共识

### 步骤 4: 输出结论

汇总讨论结果，输出结构化报告。

---

## ⛔ MCP 工具与对话输出分离规则

**核心原则：MCP 返回值是内部状态，不是给用户看的。Agent 必须在对话中生成完整报告。**

### 强制约束

1. **MCP 返回值不得直接展示** — `reqflow_stage_report`、`reqflow_dispatch_agent` 返回的是 JSON 状态，不是格式化报告
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

### MCP 即时反馈

每次调用 MCP 工具后，必须在对话中输出一行反馈：

```
📡 reqflow_report(stage="PRD理解") → ✅ 已记录 (阶段 2/11, 18%)
📡 reqflow_verify(gate="tdd-gate") → ❌ 未通过: failing_tests_count 缺失
🔧 修复计划: 编写失败测试后重新提交
```

⛔ **禁止静默调用 MCP 工具不输出。**

---

## 讨论轮次详细反馈

### 讨论轮次反馈模板

```
### 📡 讨论轮次 {round}：{stage_name}

**主 Agent 角色：**

📋 **research-agent** — 调研需求背景、竞品方案
- 🔍 调研方法: 竞品分析 + 技术调研
- 📊 发现: {finding}
- 💡 建议: {suggestion}
- 🎯 置信度: {confidence}%

🏗️ **architecture-agent** — 分析现有架构、评估影响
- 🔍 分析方法: 代码图 + 依赖分析
- 📊 发现: {finding}
- 💡 建议: {suggestion}
- 🎯 置信度: {confidence}%

🔒 **security-agent** — 评估安全风险、合规要求
- 🔍 评估方法: 安全扫描 + 合规检查
- 📊 发现: {finding}
- 💡 建议: {suggestion}
- 🎯 置信度: {confidence}%

**辅助 Worker 角色：**

🔧 **code-search-agent** — 搜索相关代码
- 📁 找到文件: {files}
- 📝 相关代码: {code_snippet}

🔧 **test-search-agent** — 搜索现有测试
- 📁 找到测试: {test_files}
- 📝 覆盖场景: {scenarios}

**轮次摘要：**
- 共识点: {consensus_points}
- 分歧点: {dissent_points}
- 下一轮聚焦: {next_focus}
```

### 共识确认反馈模板

```
### 📊 共识确认：{stage_name}

**最终结论:** {consensus}

**置信度评估:**
| 维度 | 分数 | 进度 | 热力 | 趋势 |
|------|------|------|------|------|
| 完整性 | {score} | {bar} | {heat} | {trend} |
| 一致性 | {score} | {bar} | {heat} | {trend} |
| 准确性 | {score} | {bar} | {heat} | {trend} |
| 可测试性 | {score} | {bar} | {heat} | {trend} |
| 风险覆盖 | {score} | {bar} | {heat} | {trend} |
| Spec合规 | {score} | {bar} | {heat} | {trend} |
**综合: {overall_score} ({level})**

**讨论统计:**
- 总轮次: {total_rounds}
- 参与 Agent: {agent_count}
- 参与 Worker: {worker_count}
- 分歧解决: {resolved_count}
- 共识达成: ✅

📡 reqflow_consensus(stage="{stage_name}") → ✅ 共识达成 (置信度 {confidence}%, {rounds} 轮讨论)
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
  | xxx.java | 修改 | ✅ | 通过 |
  产物完整性: 1/1 通过
  ```

---

## 相关 Skills

- `dispatcher` — 调度器，路由分析和工作流加载
- `discovery` — 上下文发现阶段
- `prd-review` — 独立 PRD 审查（可单独使用）

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
