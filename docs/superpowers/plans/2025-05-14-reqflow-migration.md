# ReqFlow 迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 requirement-flow-plugin 重构为 ReqFlow — 一个 model-agnostic 的 6 层工作流框架

**Architecture:** 围绕6个核心能力层（context/tools/orchestration/state/evaluation/constraints）重组现有skill，新增运行时抽象层支持多模型接入

**Tech Stack:** Python, YAML, Markdown

---

## 文件结构总览

```
reqflow/                            ← 新项目根目录（从 requirement-flow-plugin 迁移）
├── context/                        ← 01 上下文管理
│   ├── __init__.py
│   ├── bootstrap.py                # 从 skills/context-bootstrap/ 迁移
│   ├── pack_builder.py             # 从 skills/context-pack-builder/ 迁移
│   ├── discovery.py                # 从 skills/java-context-engine/ 迁移
│   ├── code_graph.py               # 从 skills/java-code-graph/ 迁移
│   ├── semantic_index.py           # 从 skills/java-semantic-index/ 迁移
│   ├── impact.py                   # 从 skills/java-impact-analysis/ 迁移
│   └── standards.py                # 从 skills/coding-standards/ 迁移
├── tools/                          ← 02 工具系统
│   ├── __init__.py
│   ├── registry.py                 # 新建：工具注册表
│   ├── build.py                    # 从 skills/build/ 迁移
│   ├── deploy.py                   # 从 skills/deploy/ 迁移
│   ├── adapter_factory.py          # 从 skills/adapter-factory/ 迁移
│   ├── verify_api.py               # 从 skills/verify-api/ 迁移
│   ├── verify_ui.py                # 从 skills/verify-ui/ 迁移
│   ├── verify_message.py           # 从 skills/verify-message/ 迁移
│   ├── verify_rpc.py               # 从 skills/verify-rpc/ 迁移
│   └── infra_catalog.py            # 从 skills/infra-components/ 迁移
├── orchestration/                  ← 03 执行编排
│   ├── __init__.py
│   ├── main_flow.py                # 从 skills/main-flow/ 迁移
│   ├── workflow_run.py             # 从 skills/workflow-run/ 迁移
│   ├── loop_engine.py              # 从 skills/loop-engine/ 迁移
│   ├── agent_coordinator.py        # 从 skills/agent-coordinator/ 迁移
│   ├── java_agent_coordinator.py   # 从 skills/java-agent-coordinator/ 迁移
│   ├── router.py                   # 从 skills/requirement-router/ 迁移
│   └── plan_executor.py            # 新建：计划执行（吸收 writing-plans + executing-plans）
├── state/                          ← 04 状态与记忆
│   ├── __init__.py
│   ├── session.py                  # 新建：会话级持久上下文
│   ├── memory.py                   # 新建：三层记忆系统
│   ├── checkpoint.py               # 新建：检查点恢复
│   ├── evolution.py                # 从 skills/evolution-proposal/ 迁移
│   ├── checklist.py                # 从 skills/dynamic-checklist/ 迁移
│   └── intelligence.py             # 从 skills/workflow-intelligence/ 迁移
├── evaluation/                     ← 05 评估与观测
│   ├── __init__.py
│   ├── tracer.py                   # 新建：执行追踪
│   ├── quality_gates.py            # 从 skills/quality-gates/ 迁移
│   ├── compliance.py               # 从 skills/compliance-report/ 迁移
│   ├── test_plan.py                # 从 skills/test-plan/ 迁移
│   ├── completion_gate.py          # 从 skills/completion-gate/ 迁移
│   └── code_review.py              # 新建：代码审查双向流程
├── constraints/                    ← 06 约束与恢复
│   ├── __init__.py
│   ├── constitution.py             # 从 skills/constitution-check/ 迁移
│   ├── design_gate.py              # 从 skills/design-gate/ 迁移
│   ├── tdd_gate.py                 # 从 skills/tdd-gate/ 迁移
│   ├── spec_governance.py          # 从 skills/spec-governance/ 迁移
│   ├── spec_delta.py               # 从 skills/spec-delta/ 迁移
│   ├── spec_archive.py             # 从 skills/spec-archive/ 迁移
│   ├── guardrails.py               # 新建：并行约束验证
│   ├── file_boundary.py            # 新建：文件编辑边界控制
│   └── debug_strategy.py           # 新建：结构化调试策略
├── runtime/                        ← 模型运行时抽象层
│   ├── runtime_config.py           # 新建：RuntimeConfig 接口
│   ├── registry.py                 # 新建：运行时注册表
│   └── providers/
│       ├── claude.yaml             # 新建
│       ├── gpt.yaml                # 新建
│       ├── gemini.yaml             # 新建
│       ├── deepseek.yaml           # 新建
│       └── manual.yaml             # 新建
├── agents/                         ← 从 agents/ 迁移
│   ├── dev_agent.md
│   ├── verify_agent.md
│   ├── review_agent.md
│   ├── build_agent.md
│   ├── deploy_agent.md
│   └── test_plan_agent.md
├── scripts/                        ← 从 scripts/ 精简迁移
├── templates/                      ← 从 templates/ 迁移
├── docs/                           ← 从 docs/ 迁移
├── commands/                       ← 从 commands/ 迁移
├── hooks/                          ← 从 hooks/ 迁移
├── README.md                       # 重写
└── CHANGELOG.md                    # 重写
```

---

## Task 1: 创建 ReqFlow 目录骨架

**Files:**
- Create: `reqflow/` 及所有子目录
- Create: 所有 `__init__.py`

- [ ] **Step 1: 创建6层目录结构**

```bash
cd /Users/yuanjulong/Documents/ai_flow
mkdir -p reqflow/{context,tools,orchestration,state,evaluation,constraints}
mkdir -p reqflow/runtime/providers
mkdir -p reqflow/agents
mkdir -p reqflow/scripts
mkdir -p reqflow/templates
mkdir -p reqflow/docs
mkdir -p reqflow/commands
mkdir -p reqflow/hooks
```

- [ ] **Step 2: 创建所有 __init__.py**

```bash
for dir in context tools orchestration state evaluation constraints; do
  touch reqflow/$dir/__init__.py
done
```

- [ ] **Step 3: 验证目录结构**

```bash
find reqflow -type d | sort
```

Expected: 14 directories listed

- [ ] **Step 4: Commit**

```bash
git add reqflow/
git commit -m "feat: create ReqFlow directory skeleton with 6 core layers"
```

---

## Task 2: 迁移 context 层（01 上下文管理）

**Files:**
- Create: `reqflow/context/bootstrap.py`
- Create: `reqflow/context/pack_builder.py`
- Create: `reqflow/context/discovery.py`
- Create: `reqflow/context/code_graph.py`
- Create: `reqflow/context/semantic_index.py`
- Create: `reqflow/context/impact.py`
- Create: `reqflow/context/standards.py`

- [ ] **Step 1: 迁移 context-bootstrap**

```bash
cp requirement-flow-plugin/skills/context-bootstrap/SKILL.md reqflow/context/bootstrap.md
```

- [ ] **Step 2: 迁移 context-pack-builder**

```bash
cp requirement-flow-plugin/skills/context-pack-builder/SKILL.md reqflow/context/pack_builder.md
```

- [ ] **Step 3: 迁移 java-context-engine**

```bash
cp requirement-flow-plugin/skills/java-context-engine/SKILL.md reqflow/context/discovery.md
```

- [ ] **Step 4: 迁移 java-code-graph**

```bash
cp requirement-flow-plugin/skills/java-code-graph/SKILL.md reqflow/context/code_graph.md
```

- [ ] **Step 5: 迁移 java-semantic-index**

```bash
cp requirement-flow-plugin/skills/java-semantic-index/SKILL.md reqflow/context/semantic_index.md
```

- [ ] **Step 6: 迁移 java-impact-analysis**

```bash
cp requirement-flow-plugin/skills/java-impact-analysis/SKILL.md reqflow/context/impact.md
```

- [ ] **Step 7: 迁移 coding-standards**

```bash
cp requirement-flow-plugin/skills/coding-standards/SKILL.md reqflow/context/standards.md
```

- [ ] **Step 8: 创建 context/__init__.py 模块索引**

```python
"""ReqFlow Context Management Layer - 01 上下文管理

模型到底看到了什么。
"""
```

- [ ] **Step 9: 验证文件完整性**

```bash
ls -la reqflow/context/
```

Expected: 8 files (7 .md + 1 __init__.py)

- [ ] **Step 10: Commit**

```bash
git add reqflow/context/
git commit -m "feat(context): migrate context management layer from skills"
```

---

## Task 3: 迁移 tools 层（02 工具系统）

**Files:**
- Create: `reqflow/tools/registry.md`（新建工具注册表文档）
- Create: `reqflow/tools/build.md`
- Create: `reqflow/tools/deploy.md`
- Create: `reqflow/tools/adapter_factory.md`
- Create: `reqflow/tools/verify_api.md`
- Create: `reqflow/tools/verify_ui.md`
- Create: `reqflow/tools/verify_message.md`
- Create: `reqflow/tools/verify_rpc.md`
- Create: `reqflow/tools/infra_catalog.md`

- [ ] **Step 1: 迁移 build**

```bash
cp requirement-flow-plugin/skills/build/SKILL.md reqflow/tools/build.md
```

- [ ] **Step 2: 迁移 deploy**

```bash
cp requirement-flow-plugin/skills/deploy/SKILL.md reqflow/tools/deploy.md
```

- [ ] **Step 3: 迁移 adapter-factory**

```bash
cp requirement-flow-plugin/skills/adapter-factory/SKILL.md reqflow/tools/adapter_factory.md
```

- [ ] **Step 4: 迁移 verify-api**

```bash
cp requirement-flow-plugin/skills/verify-api/SKILL.md reqflow/tools/verify_api.md
```

- [ ] **Step 5: 迁移 verify-ui**

```bash
cp requirement-flow-plugin/skills/verify-ui/SKILL.md reqflow/tools/verify_ui.md
```

- [ ] **Step 6: 迁移 verify-message**

```bash
cp requirement-flow-plugin/skills/verify-message/SKILL.md reqflow/tools/verify_message.md
```

- [ ] **Step 7: 迁移 verify-rpc**

```bash
cp requirement-flow-plugin/skills/verify-rpc/SKILL.md reqflow/tools/verify_rpc.md
```

- [ ] **Step 8: 迁移 infra-components**

```bash
cp requirement-flow-plugin/skills/infra-components/SKILL.md reqflow/tools/infra_catalog.md
```

- [ ] **Step 9: 创建工具注册表文档**

```bash
cat > reqflow/tools/registry.md << 'EOF'
# Tool Registry

工具注册机制，定义模型可用的工具集。

## 注册格式

```yaml
tools:
  registered:
    - name: build
      type: local_command
      command: "mvn clean test"
    - name: deploy
      type: provider_adapter
      adapter: ".dev-workflow/adapters/deploy-adapter.py"
    - name: verify-api
      type: manual_checklist
      template: "templates/verify-api-checklist.md"
```

## 工具类型

| type | 说明 |
|------|------|
| local_command | 本地shell命令 |
| provider_adapter | 外部provider适配器脚本 |
| manual_checklist | 人工执行checklist |
EOF
```

- [ ] **Step 10: Commit**

```bash
git add reqflow/tools/
git commit -m "feat(tools): migrate tool system layer from skills"
```

---

## Task 4: 迁移 orchestration 层（03 执行编排）

**Files:**
- Create: `reqflow/orchestration/main_flow.md`
- Create: `reqflow/orchestration/workflow_run.md`
- Create: `reqflow/orchestration/loop_engine.md`
- Create: `reqflow/orchestration/agent_coordinator.md`
- Create: `reqflow/orchestration/java_agent_coordinator.md`
- Create: `reqflow/orchestration/router.md`
- Create: `reqflow/orchestration/plan_executor.md`（新建）

- [ ] **Step 1: 迁移 main-flow**

```bash
cp requirement-flow-plugin/skills/main-flow/SKILL.md reqflow/orchestration/main_flow.md
```

- [ ] **Step 2: 迁移 workflow-run**

```bash
cp requirement-flow-plugin/skills/workflow-run/SKILL.md reqflow/orchestration/workflow_run.md
```

- [ ] **Step 3: 迁移 loop-engine**

```bash
cp requirement-flow-plugin/skills/loop-engine/SKILL.md reqflow/orchestration/loop_engine.md
```

- [ ] **Step 4: 迁移 agent-coordinator**

```bash
cp requirement-flow-plugin/skills/agent-coordinator/SKILL.md reqflow/orchestration/agent_coordinator.md
```

- [ ] **Step 5: 迁移 java-agent-coordinator**

```bash
cp requirement-flow-plugin/skills/java-agent-coordinator/SKILL.md reqflow/orchestration/java_agent_coordinator.md
```

- [ ] **Step 6: 迁移 requirement-router**

```bash
cp requirement-flow-plugin/skills/requirement-router/SKILL.md reqflow/orchestration/router.md
```

- [ ] **Step 7: 创建 plan_executor.md**

```bash
cat > reqflow/orchestration/plan_executor.md << 'EOF'
# Plan Executor

计划编写与执行方法论，吸收自 superpowers writing-plans + executing-plans。

## 计划编写原则

1. 每个步骤是单一动作（2-5分钟）
2. 包含完整代码，不留占位符
3. 精确文件路径
4. 精确命令和预期输出

## 执行模式

### 串行执行（默认）
按任务顺序逐个执行，每个任务完成后验证再继续。

### 并行执行（可选）
独立任务可并行调度：
```python
async def dispatch_parallel(items, coordinator):
    tasks = [coordinator.dispatch(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

## 检查点

每个任务完成后自动创建 checkpoint，支持从任意点 resume。
EOF
```

- [ ] **Step 8: Commit**

```bash
git add reqflow/orchestration/
git commit -m "feat(orchestration): migrate orchestration layer from skills"
```

---

## Task 5: 迁移 state 层（04 状态与记忆）

**Files:**
- Create: `reqflow/state/session.md`（新建）
- Create: `reqflow/state/memory.md`（新建）
- Create: `reqflow/state/checkpoint.md`（新建）
- Create: `reqflow/state/evolution.md`
- Create: `reqflow/state/checklist.md`
- Create: `reqflow/state/intelligence.md`

- [ ] **Step 1: 迁移 evolution-proposal**

```bash
cp requirement-flow-plugin/skills/evolution-proposal/SKILL.md reqflow/state/evolution.md
```

- [ ] **Step 2: 迁移 dynamic-checklist**

```bash
cp requirement-flow-plugin/skills/dynamic-checklist/SKILL.md reqflow/state/checklist.md
```

- [ ] **Step 3: 迁移 workflow-intelligence**

```bash
cp requirement-flow-plugin/skills/workflow-intelligence/SKILL.md reqflow/state/intelligence.md
```

- [ ] **Step 4: 创建 session.md**

```bash
cat > reqflow/state/session.md << 'EOF'
# Session Management

会话级持久上下文管理，维护 agent loop 内的工作状态。

## 职责

- 管理当前会话的工作上下文
- 维护跨轮次的对话历史摘要
- 支持子智能体 resume 时的上下文恢复

## 会话状态

```yaml
session:
  session_id: <uuid>
  working_context:
    current_task: <task_description>
    relevant_files: []
    decisions_made: []
  conversation_summary: ""
  created_at: <timestamp>
  last_active: <timestamp>
```

## 与 state.json 的关系

- state.json 是 run 级别的持久状态
- session 是会话级别的工作上下文
- session 在 run 结束后可选择保留或丢弃
EOF
```

- [ ] **Step 5: 创建 memory.md**

```bash
cat > reqflow/state/memory.md << 'EOF'
# Memory System

三层记忆系统，参考 CrewAI 的多层记忆设计。

## 三层结构

### Short-term Memory（短期记忆）
当前 run 的上下文，替代单一的 state.json。

### Long-term Memory（长期记忆）
跨 run 的经验教训积累，替代单一的 lessons_learned 字段。

### Entity Memory（实体记忆）
项目级知识图谱：类、模块、接口的关系。

## 记忆格式

```yaml
memory:
  short_term:
    - key: "current-work-item"
      value: "implement user auth"
      timestamp: "2025-05-14T10:00:00"
  long_term:
    - lesson: "JWT token 过期时间不要超过 24h"
      source: "run-2025-05-10"
      category: "security"
  entity:
    - name: "UserService"
      type: "class"
      location: "src/main/java/service/UserService.java"
      dependencies: ["UserRepository", "JwtProvider"]
```
EOF
```

- [ ] **Step 6: 创建 checkpoint.md**

```bash
cat > reqflow/state/checkpoint.md << 'EOF'
# Checkpoint System

检查点恢复机制，参考 CrewAI 的 checkpointing 设计。

## 职责

- 每个 stage 完成后自动创建 checkpoint
- 支持从任意 checkpoint resume
- checkpoint 包含 state + context + log

## Checkpoint 结构

```yaml
checkpoint:
  checkpoint_id: <uuid>
  run_id: <run_id>
  stage: <stage_name>
  timestamp: <timestamp>
  state_snapshot: .dev-workflow/runs/<run_id>/checkpoints/<id>/state.json
  context_snapshot: .dev-workflow/runs/<run_id>/checkpoints/<id>/context.json
  log_snapshot: .dev-workflow/runs/<run_id>/checkpoints/<id>/execution.log
```

## Resume 流程

1. 加载指定 checkpoint 的 state_snapshot
2. 恢复 context_snapshot
3. 从该 stage 继续执行
EOF
```

- [ ] **Step 7: Commit**

```bash
git add reqflow/state/
git commit -m "feat(state): migrate state layer + add session/memory/checkpoint modules"
```

---

## Task 6: 迁移 evaluation 层（05 评估与观测）

**Files:**
- Create: `reqflow/evaluation/tracer.md`（新建）
- Create: `reqflow/evaluation/quality_gates.md`
- Create: `reqflow/evaluation/compliance.md`
- Create: `reqflow/evaluation/test_plan.md`
- Create: `reqflow/evaluation/completion_gate.md`
- Create: `reqflow/evaluation/code_review.md`（新建）

- [ ] **Step 1: 迁移 quality-gates**

```bash
cp requirement-flow-plugin/skills/quality-gates/SKILL.md reqflow/evaluation/quality_gates.md
```

- [ ] **Step 2: 迁移 compliance-report**

```bash
cp requirement-flow-plugin/skills/compliance-report/SKILL.md reqflow/evaluation/compliance.md
```

- [ ] **Step 3: 迁移 test-plan**

```bash
cp requirement-flow-plugin/skills/test-plan/SKILL.md reqflow/evaluation/test_plan.md
```

- [ ] **Step 4: 迁移 completion-gate**

```bash
cp requirement-flow-plugin/skills/completion-gate/SKILL.md reqflow/evaluation/completion_gate.md
```

- [ ] **Step 5: 创建 tracer.md**

```bash
cat > reqflow/evaluation/tracer.md << 'EOF'
# Execution Tracer

执行追踪系统，参考 OpenAI Agents SDK 的 hierarchical trace/span 模型。

## Trace 结构

```yaml
trace:
  run_id: <id>
  spans:
    - span_id: <id>
      parent_id: <parent>
      name: "agent.dev-agent.work-item-3"
      input: <context_pack>
      output: <dev_report>
      duration_ms: <n>
      tokens: {input: <n>, output: <n>}
      status: success|failure
```

## 职责

- 记录每次 agent 调用的输入、输出、耗时、token 用量
- 支持 trace 导出用于调试和优化
- 与 state 层的 session 配合，提供完整的执行历史
EOF
```

- [ ] **Step 6: 创建 code_review.md**

```bash
cat > reqflow/evaluation/code_review.md << 'EOF'
# Code Review

代码审查双向流程，吸收自 superpowers requesting-code-review + receiving-code-review。

## 流程

### 1. Request Review
- 开发智能体完成编码后，生成 review request
- 包含：changed files, diff, test results, self-assessment

### 2. Receive Review
- 审查智能体（只读）分析代码
- 输出：issues found (severity: critical/major/minor), suggestions

### 3. Address Feedback
- 开发智能体接收审查反馈
- 修复 critical 和 major issues
- 记录 decisions（接受/拒绝/延迟）

## 审查维度

| 维度 | 检查内容 |
|------|---------|
| 功能正确性 | 是否满足需求 |
| 代码规范 | 是否符合 coding-standards |
| 测试覆盖 | 是否有充分测试 |
| 安全性 | 是否有安全漏洞 |
| 性能 | 是否有性能问题 |
EOF
```

- [ ] **Step 7: Commit**

```bash
git add reqflow/evaluation/
git commit -m "feat(evaluation): migrate evaluation layer + add tracer/code_review modules"
```

---

## Task 7: 迁移 constraints 层（06 约束与恢复）

**Files:**
- Create: `reqflow/constraints/constitution.md`
- Create: `reqflow/constraints/design_gate.md`
- Create: `reqflow/constraints/tdd_gate.md`
- Create: `reqflow/constraints/spec_governance.md`
- Create: `reqflow/constraints/spec_delta.md`
- Create: `reqflow/constraints/spec_archive.md`
- Create: `reqflow/constraints/guardrails.md`（新建）
- Create: `reqflow/constraints/file_boundary.md`（新建）
- Create: `reqflow/constraints/debug_strategy.md`（新建）

- [ ] **Step 1: 迁移 constitution-check**

```bash
cp requirement-flow-plugin/skills/constitution-check/SKILL.md reqflow/constraints/constitution.md
```

- [ ] **Step 2: 迁移 design-gate**

```bash
cp requirement-flow-plugin/skills/design-gate/SKILL.md reqflow/constraints/design_gate.md
```

- [ ] **Step 3: 迁移 tdd-gate**

```bash
cp requirement-flow-plugin/skills/tdd-gate/SKILL.md reqflow/constraints/tdd_gate.md
```

- [ ] **Step 4: 迁移 spec-governance**

```bash
cp requirement-flow-plugin/skills/spec-governance/SKILL.md reqflow/constraints/spec_governance.md
```

- [ ] **Step 5: 迁移 spec-delta**

```bash
cp requirement-flow-plugin/skills/spec-delta/SKILL.md reqflow/constraints/spec_delta.md
```

- [ ] **Step 6: 迁移 spec-archive**

```bash
cp requirement-flow-plugin/skills/spec-archive/SKILL.md reqflow/constraints/spec_archive.md
```

- [ ] **Step 7: 创建 guardrails.md**

```bash
cat > reqflow/constraints/guardrails.md << 'EOF'
# Guardrails

并行约束验证 + 快速失败机制，参考 OpenAI Agents SDK。

## 设计

约束检查与 agent 执行并行运行，检查不通过时立即失败，不等 agent 完成。

## 执行模式

```python
async def run_with_guardrails(agent_task, constraints):
    agent_result, constraint_results = await asyncio.gather(
        agent_task,
        run_constraints(constraints)
    )
    if any_failed(constraint_results):
        return FAIL_FAST
    return agent_result
```

## 约束类型

| 约束 | 检查时机 | 失败行为 |
|------|---------|---------|
| constitution | 每次 agent 调用前 | 立即阻断 |
| file_boundary | 每次文件编辑时 | 立即阻断 |
| design_gate | 实现前 | 需要审批 |
| tdd_gate | 行为变更前 | 提示使用 TDD |
EOF
```

- [ ] **Step 8: 创建 file_boundary.md**

```bash
cat > reqflow/constraints/file_boundary.md << 'EOF'
# File Boundary Control

文件编辑边界控制，防止子智能体越权编辑。吸收自 freeze (garrytan)。

## 规则

- 子智能体只能编辑 authorized scope 内的文件
- 主智能体可以显式扩展 scope
- 任何 scope 外的编辑尝试被阻断并记录

## 边界定义

```yaml
file_boundary:
  authorized_scope:
    - "src/main/java/service/**"
    - "src/test/java/service/**"
  denied_scope:
    - "src/main/java/config/**"
    - ".dev-workflow/**"
  expansion_policy: "coordinator_approval"  # 需要主智能体审批
```

## 与 agent 模板配合

每个 agent 模板的 frontmatter 中声明默认 scope，主智能体在调度时注入实际 scope。
EOF
```

- [ ] **Step 9: 创建 debug_strategy.md**

```bash
cat > reqflow/constraints/debug_strategy.md << 'EOF'
# Debug Strategy

结构化调试策略，吸收自 superpowers systematic-debugging。

## 调试流程

1. **Observe（观察）**：收集错误信息、日志、堆栈
2. **Classify（分类）**：判断错误类型（编译/运行时/逻辑/集成）
3. **Hypothesize（假设）**：提出可能的原因
4. **Verify（验证）**：设计实验验证假设
5. **Fix（修复）**：实施最小修复
6. **Regression（回归）**：确认修复不引入新问题

## 与 loop-engine 配合

loop-engine 的 observe→classify→localize→patch→verify→review→decide 流程中，debug_strategy 增强了 classify 和 localize 阶段。

## 分类矩阵

| 错误类型 | 特征 | 常见原因 |
|---------|------|---------|
| 编译错误 | 类型不匹配、缺少导入 | API 变更、版本不兼容 |
| 运行时异常 | NPE、ClassCastException | 空值未检查、类型转换错误 |
| 逻辑错误 | 输出不符预期 | 边界条件、算法错误 |
| 集成错误 | 接口调用失败 | 契约不一致、序列化问题 |
EOF
```

- [ ] **Step 10: Commit**

```bash
git add reqflow/constraints/
git commit -m "feat(constraints): migrate constraints layer + add guardrails/file_boundary/debug_strategy"
```

---

## Task 8: 创建运行时抽象层

**Files:**
- Create: `reqflow/runtime/runtime_config.py`
- Create: `reqflow/runtime/registry.py`
- Create: `reqflow/runtime/providers/claude.yaml`
- Create: `reqflow/runtime/providers/gpt.yaml`
- Create: `reqflow/runtime/providers/gemini.yaml`
- Create: `reqflow/runtime/providers/deepseek.yaml`
- Create: `reqflow/runtime/providers/manual.yaml`

- [ ] **Step 1: 创建 runtime_config.py**

```python
"""RuntimeConfig interface for model-agnostic runtime abstraction."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Capabilities:
    supports_agent_tools: bool = True
    supports_bash: bool = True
    supports_file_edit: bool = True
    supports_image: bool = False
    max_context_tokens: int = 200000


@dataclass
class ToolMapping:
    read_file: str = "Read"
    edit_file: str = "Edit"
    bash: str = "Bash"
    agent: Optional[str] = "Agent"


@dataclass
class ContextFormat:
    system_prompt_template: str = "templates/system-prompt.md"
    skill_format: str = "markdown"
    artifact_format: str = "markdown"


@dataclass
class RuntimePaths:
    run_dir: str = ".dev-workflow/runs/"
    state_file: str = "state.json"
    log_file: str = "execution.log"


@dataclass
class RuntimeConfig:
    name: str
    display_name: str
    capabilities: Capabilities = field(default_factory=Capabilities)
    tool_mapping: ToolMapping = field(default_factory=ToolMapping)
    context_format: ContextFormat = field(default_factory=ContextFormat)
    paths: RuntimePaths = field(default_factory=RuntimePaths)
```

- [ ] **Step 2: 创建 registry.py**

```python
"""Runtime registry for managing multiple runtime configs."""

import yaml
from pathlib import Path
from .runtime_config import RuntimeConfig, Capabilities, ToolMapping, ContextFormat, RuntimePaths


class RuntimeRegistry:
    def __init__(self, providers_dir: str = None):
        if providers_dir is None:
            providers_dir = str(Path(__file__).parent / "providers")
        self.providers_dir = Path(providers_dir)
        self._configs: dict[str, RuntimeConfig] = {}
        self._load_all()

    def _load_all(self):
        for yaml_file in self.providers_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            config = self._from_dict(data)
            self._configs[config.name] = config

    def _from_dict(self, data: dict) -> RuntimeConfig:
        caps = Capabilities(**data.get("capabilities", {}))
        tools = ToolMapping(**data.get("tool_mapping", {}))
        fmt = ContextFormat(**data.get("context_format", {}))
        paths = RuntimePaths(**data.get("paths", {}))
        return RuntimeConfig(
            name=data["name"],
            display_name=data["display_name"],
            capabilities=caps,
            tool_mapping=tools,
            context_format=fmt,
            paths=paths,
        )

    def get(self, name: str) -> RuntimeConfig:
        if name not in self._configs:
            raise ValueError(f"Unknown runtime: {name}. Available: {list(self._configs.keys())}")
        return self._configs[name]

    def list_runtimes(self) -> list[str]:
        return list(self._configs.keys())
```

- [ ] **Step 3: 创建 claude.yaml**

```yaml
name: claude
display_name: "Claude Code"

capabilities:
  supports_agent_tools: true
  supports_bash: true
  supports_file_edit: true
  supports_image: true
  max_context_tokens: 200000

tool_mapping:
  read_file: "Read"
  edit_file: "Edit"
  bash: "Bash"
  agent: "Agent"

context_format:
  system_prompt_template: "templates/system-prompt.md"
  skill_format: "markdown"
  artifact_format: "markdown"

paths:
  run_dir: ".dev-workflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 4: 创建 gpt.yaml**

```yaml
name: gpt
display_name: "GPT-4o"

capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  supports_image: true
  max_context_tokens: 128000

tool_mapping:
  read_file: "functions.read_file"
  edit_file: "functions.edit_file"
  bash: "functions.run_command"
  agent: null

context_format:
  system_prompt_template: "templates/system-prompt-gpt.md"
  skill_format: "json"
  artifact_format: "json"

paths:
  run_dir: ".dev-workflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 5: 创建 gemini.yaml**

```yaml
name: gemini
display_name: "Gemini Pro"

capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  supports_image: true
  max_context_tokens: 1000000

tool_mapping:
  read_file: "functions.read_file"
  edit_file: "functions.edit_file"
  bash: "functions.run_command"
  agent: null

context_format:
  system_prompt_template: "templates/system-prompt-gemini.md"
  skill_format: "markdown"
  artifact_format: "markdown"

paths:
  run_dir: ".dev-workflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 6: 创建 deepseek.yaml**

```yaml
name: deepseek
display_name: "DeepSeek"

capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  supports_image: false
  max_context_tokens: 64000

tool_mapping:
  read_file: "functions.read_file"
  edit_file: "functions.edit_file"
  bash: "functions.run_command"
  agent: null

context_format:
  system_prompt_template: "templates/system-prompt-deepseek.md"
  skill_format: "markdown"
  artifact_format: "markdown"

paths:
  run_dir: ".dev-workflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 7: 创建 manual.yaml**

```yaml
name: manual
display_name: "Manual Mode"

capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  supports_image: false
  max_context_tokens: 0

tool_mapping:
  read_file: "manual"
  edit_file: "manual"
  bash: "manual"
  agent: null

context_format:
  system_prompt_template: "templates/system-prompt-manual.md"
  skill_format: "markdown"
  artifact_format: "markdown"

paths:
  run_dir: ".dev-workflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 8: Commit**

```bash
git add reqflow/runtime/
git commit -m "feat(runtime): create runtime abstraction layer with 5 provider configs"
```

---

## Task 9: 迁移 agents、scripts、templates、commands、hooks

**Files:**
- Copy: `agents/*.md` → `reqflow/agents/`
- Copy: `scripts/*.py` → `reqflow/scripts/`
- Copy: `templates/` → `reqflow/templates/`
- Copy: `commands/*.md` → `reqflow/commands/`
- Copy: `hooks/hooks.json` → `reqflow/hooks/`

- [ ] **Step 1: 迁移 agents**

```bash
cp requirement-flow-plugin/agents/*.md reqflow/agents/
```

- [ ] **Step 2: 迁移 scripts**

```bash
cp requirement-flow-plugin/scripts/*.py reqflow/scripts/
cp requirement-flow-plugin/scripts/*.sh reqflow/scripts/
```

- [ ] **Step 3: 迁移 templates**

```bash
cp -r requirement-flow-plugin/templates/* reqflow/templates/
```

- [ ] **Step 4: 迁移 commands**

```bash
cp requirement-flow-plugin/commands/*.md reqflow/commands/
```

- [ ] **Step 5: 迁移 hooks**

```bash
cp requirement-flow-plugin/hooks/hooks.json reqflow/hooks/
```

- [ ] **Step 6: 迁移 docs**

```bash
cp requirement-flow-plugin/docs/*.md reqflow/docs/
```

- [ ] **Step 7: Commit**

```bash
git add reqflow/agents reqflow/scripts reqflow/templates reqflow/commands reqflow/hooks reqflow/docs
git commit -m "feat: migrate agents, scripts, templates, commands, hooks, docs"
```

---

## Task 10: 删除 support skills + 更新索引

**Files:**
- Delete: `requirement-flow-plugin/skills/support-*`（49个目录）
- Modify: `requirement-flow-plugin/skills/SKILL-INDEX.md`

- [ ] **Step 1: 删除所有 support skills**

```bash
cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin
rm -rf skills/support-*
```

- [ ] **Step 2: 验证删除结果**

```bash
ls skills/ | grep -c "^support-"
```

Expected: 0

- [ ] **Step 3: 验证保留的核心 skills**

```bash
ls skills/ | grep -v "^support-" | grep -v "^SKILL-INDEX"
```

Expected: 36 core skills

- [ ] **Step 4: 更新 SKILL-INDEX.md**

重写 SKILL-INDEX.md，只保留核心 skills，移除所有 support 类别。

- [ ] **Step 5: Commit**

```bash
git add skills/
git commit -m "chore: remove 49 support skills, update SKILL-INDEX"
```

---

## Task 11: 创建 README.md

**Files:**
- Create: `reqflow/README.md`

- [ ] **Step 1: 创建 README.md**

基于设计文档创建新的 README.md，包含：
- 项目简介（ReqFlow 是什么）
- 6 核心能力层说明
- 快速开始
- 目录结构
- 运行时配置
- 从 requirement-flow-plugin 迁移指南

- [ ] **Step 2: Commit**

```bash
git add reqflow/README.md
git commit -m "docs: create ReqFlow README"
```

---

## Task 12: 整合外部 Skill 方法论

**Files:**
- Create: `reqflow/_external/` 目录存放下载的原始 skill
- Modify: 对应的 constraints/evaluation/orchestration 模块

- [ ] **Step 1: 创建外部 skill 下载目录**

```bash
mkdir -p reqflow/_external
```

- [ ] **Step 2: 下载 systematic-debugging**

从 skills.sh 或 GitHub 下载 obra/superpowers 的 systematic-debugging skill，存入 `reqflow/_external/systematic-debugging/`

- [ ] **Step 3: 下载 subagent-driven-development**

从 skills.sh 或 GitHub 下载 obra/superpowers 的 subagent-driven-development skill，存入 `reqflow/_external/subagent-driven-development/`

- [ ] **Step 4: 下载 dispatching-parallel-agents**

从 skills.sh 或 GitHub 下载 obra/superpowers 的 dispatching-parallel-agents skill，存入 `reqflow/_external/dispatching-parallel-agents/`

- [ ] **Step 5: 下载 code-review 相关 skills**

下载 requesting-code-review + receiving-code-review，存入 `reqflow/_external/code-review/`

- [ ] **Step 6: 下载 freeze**

从 clawhub 下载 garrytan 的 freeze skill，存入 `reqflow/_external/freeze/`

- [ ] **Step 7: 分析并整合到对应模块**

逐个分析下载的 skill，将核心方法论融入：
- systematic-debugging → `reqflow/constraints/debug_strategy.md`
- subagent-driven-development → `reqflow/orchestration/agent_coordinator.md`
- dispatching-parallel-agents → `reqflow/orchestration/plan_executor.md`
- code-review → `reqflow/evaluation/code_review.md`
- freeze → `reqflow/constraints/file_boundary.md`

- [ ] **Step 8: Commit**

```bash
git add reqflow/_external/ reqflow/constraints/ reqflow/evaluation/ reqflow/orchestration/
git commit -m "feat: integrate external skill methodologies"
```

---

## Task 13: 最终验证

- [ ] **Step 1: 验证目录结构完整性**

```bash
find reqflow -type f | wc -l
```

Expected: 50+ files

- [ ] **Step 2: 验证6层目录都有内容**

```bash
for dir in context tools orchestration state evaluation constraints; do
  echo "$dir: $(ls reqflow/$dir/ | wc -l) files"
done
```

Expected: 每层至少 5 个文件

- [ ] **Step 3: 验证 runtime 层**

```bash
ls reqflow/runtime/providers/
```

Expected: 5 个 yaml 文件

- [ ] **Step 4: 验证 agents 层**

```bash
ls reqflow/agents/
```

Expected: 6 个 agent 模板

- [ ] **Step 5: 验证无 support skills 残留**

```bash
ls requirement-flow-plugin/skills/ | grep "^support-" | wc -l
```

Expected: 0

- [ ] **Step 6: 最终 Commit**

```bash
git add -A
git commit -m "feat: ReqFlow migration complete - 6-layer architecture with runtime abstraction"
```
