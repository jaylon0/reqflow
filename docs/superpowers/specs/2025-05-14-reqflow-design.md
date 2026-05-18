# ReqFlow 设计文档

> 日期：2025-05-14
> 状态：待审批
> 范围：技能精简 + Plugin→ReqFlow 架构升级

## 1. 背景与目标

### 1.1 当前状态

requirement-flow-plugin 是一个 Claude Code 插件，包含：
- 86 个 skill 目录（36 核心 + 49 support + 1 索引）
- 7 个 agent 模板
- 23 个脚本
- 8 个命令入口
- 13 个文档

问题：support skills 从 skills 项目大量复制，与 Java 后端交付流程无关，项目臃肿。

### 1.2 目标

1. **技能精简**：移除 49 个无关的 support skills，只保留核心能力
2. **架构升级**：从 Claude Code plugin 升级为 model-agnostic 框架
3. **6 核心能力**：围绕上下文管理、工具系统、执行编排、状态与记忆、评估与观测、约束与恢复重新分层

### 1.3 设计原则

| 铁律 | 含义 | 在 ReqFlow 中的体现 |
|------|------|-------------------|
| 文件即记忆 | 子智能体的所有产出必须持久化到文件 | state 层所有产物持久化到 `.dev-workflow/` |
| 隔离即常态 | 每个子智能体只看到主智能体给它的信息 | context 层打包上下文，不假设外部状态 |
| 记录即保险 | 主智能体和子智能体都写日志 | orchestration 层全程结构化日志，evaluation 层可回溯审计 |

---

## 2. 总体架构

### 2.1 三层角色模型

```
┌─────────────┐
│   主智能体    │  编排者：拆任务、管状态、中转信息
│ (Orchestrator) │
└──────┬──────┘
       │
   ┌───┴───────────────┐
   │                   │
   ▼                   ▼
┌──────────┐     ┌──────────┐
│ 开发智能体 │     │ 测试智能体 │
│  (Dev)   │     │ (Tester)  │
└──────────┘     └──────────┘
```

| 角色 | 职责 | 工具权限 | 上下文管理 |
|------|------|----------|------------|
| 主智能体 | 拆任务、管计划、中转信息、写日志 | 全部 | 保持全程上下文 |
| 开发智能体 | 读需求→写代码→自测→输出 | 读写 + Bash | 每个任务新创建或 resume |
| 测试智能体 | 读需求→审查代码→输出结论 | 只读 | 每个任务新创建或 resume |

### 2.2 核心流程

```
main-flow: PRD → spec → intelligence → context → tech_plan → impl_plan → agent_exec → review → verify → archive
loop-engine: observe → classify → localize → patch → verify → review → decide
routing: L0(analyze) → L1(light-change) → L2(planned-change) → L3(delivery-loop)
```

---

## 3. 六个核心能力层

### 3.1 上下文管理（Context Management）

**解决的问题**：模型到底看到了什么

| 原技能 | 去向 | 职责 |
|--------|------|------|
| context-bootstrap | `reqflow/context/bootstrap.py` | 扫描项目结构，创建初始上下文配置 |
| context-pack-builder | `reqflow/context/pack_builder.py` | 为单个 work item 构建紧凑上下文包 |
| java-context-engine | `reqflow/context/discovery.py` | 协调代码图、语义索引、影响分析 |
| java-code-graph | `reqflow/context/code_graph.py` | ASM 字节码分析，构建调用关系图 |
| java-semantic-index | `reqflow/context/semantic_index.py` | 类摘要和方法级语义检索 |
| java-impact-analysis | `reqflow/context/impact.py` | 综合图+RAG 确定影响范围 |
| coding-standards | `reqflow/context/standards.py` | 语言/框架编码规范 |

**上下文包输出格式**：

```yaml
context_pack:
  work_item: <id>
  requirements: <精简需求>
  affected_files: <影响文件列表>
  code_snippets: <相关代码片段>
  patterns: <项目中可复用的模式>
  constraints: <版本限制、规范约束>
  lessons: <相关经验教训>
```

### 3.2 工具系统（Tool System）

**解决的问题**：模型到底能做什么

| 原技能 | 去向 | 职责 |
|--------|------|------|
| build | `reqflow/tools/build.py` | 本地构建/测试/lint |
| deploy | `reqflow/tools/deploy.py` | 部署/发布 |
| adapter-factory | `reqflow/tools/adapter_factory.py` | 生成项目级 provider 适配器 |
| verify-api | `reqflow/tools/verify_api.py` | HTTP/API 行为验证 |
| verify-ui | `reqflow/tools/verify_ui.py` | UI 集成验证 |
| verify-message | `reqflow/tools/verify_message.py` | 消息/事件验证 |
| verify-rpc | `reqflow/tools/verify_rpc.py` | 服务间调用验证 |
| infra-components | `reqflow/tools/infra_catalog.py` | 基础设施组件目录 |

**工具注册机制**：

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

### 3.3 执行编排（Execution Orchestration）

**解决的问题**：模型下一步该做什么

| 原技能 | 去向 | 职责 |
|--------|------|------|
| main-flow | `reqflow/orchestration/main_flow.py` | PRD→代码的 10 阶段管线 |
| workflow-run | `reqflow/orchestration/workflow_run.py` | 路由后的执行引擎 |
| loop-engine | `reqflow/orchestration/loop_engine.py` | 修复/反馈循环 |
| agent-coordinator | `reqflow/orchestration/agent_coordinator.py` | 子智能体调度（含并行） |
| java-agent-coordinator | `reqflow/orchestration/java_agent_coordinator.py` | Java 专用 work item 调度 |
| requirement-router | `reqflow/orchestration/router.py` | L0-L3 路由分类 |
| writing-plans + executing-plans | `reqflow/orchestration/plan_executor.py` | 计划编写与执行方法论 |

**并行 agent 调度**（新增，来自 dispatching-parallel-agents）：

```python
async def dispatch_parallel(items: list[WorkItem], coordinator):
    tasks = [coordinator.dispatch(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

### 3.4 状态与记忆（State & Memory）

**解决的问题**：系统如何跨步骤保持连续性

| 原技能 | 去向 | 职责 |
|--------|------|------|
| evolution-proposal | `reqflow/state/evolution.py` | 经验教训提取和改进建议 |
| dynamic-checklist | `reqflow/state/checklist.py` | 动态检查清单生成 |
| workflow-intelligence | `reqflow/state/intelligence.py` | 场景检测、profile、智能决策 |

**新增模块**：

| 模块 | 来源 | 职责 |
|------|------|------|
| session.py | OpenAI Agents SDK | 会话级持久上下文，跨轮次工作状态 |
| memory.py | CrewAI 三层记忆 | short_term（当前 run）、long_term（跨 run）、entity（项目知识图谱） |
| checkpoint.py | CrewAI checkpointing | 每个 stage 完成后自动 checkpoint，支持从任意点 resume |

**状态模型**：

```yaml
state:
  run_id: <id>
  current_stage: <stage_name>
  completed_modules: []
  pending_confirmations: []
  spec_status: draft|approved|archived
  quality_gates: {}
  session:
    working_context: {}
    conversation_summary: ""
  memory:
    short_term: []
    long_term: []
    entity: {}
  checkpoints:
    - stage: <name>
      timestamp: <ts>
      state_snapshot: <path>
  lessons_learned: []
  agent_execution_log: []
```

### 3.5 评估与观测（Evaluation & Observation）

**解决的问题**：系统怎么知道自己做得对不对

| 原技能 | 去向 | 职责 |
|--------|------|------|
| quality-gates | `reqflow/evaluation/quality_gates.py` | 质量门控总协调 |
| compliance-report | `reqflow/evaluation/compliance.py` | 合规报告生成 |
| test-plan | `reqflow/evaluation/test_plan.py` | 验收计划生成 |
| completion-gate | `reqflow/evaluation/completion_gate.py` | 最终完成验证 |

**新增模块**：

| 模块 | 来源 | 职责 |
|------|------|------|
| tracer.py | OpenAI Agents SDK | 执行追踪，hierarchical trace/span 模型 |
| code_review.py | superpowers requesting/receiving-code-review | 代码审查双向流程：request→receive→address |

**Trace 结构**：

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

### 3.6 约束与恢复（Constraint & Recovery）

**解决的问题**：出错了怎么办，怎么避免跑偏

| 原技能 | 去向 | 职责 |
|--------|------|------|
| constitution-check | `reqflow/constraints/constitution.py` | 项目级不可违反规则检查 |
| design-gate | `reqflow/constraints/design_gate.py` | 设计审批门控 |
| tdd-gate | `reqflow/constraints/tdd_gate.py` | TDD 适用性判断 |
| spec-governance | `reqflow/constraints/spec_governance.py` | 规格治理协调 |
| spec-delta | `reqflow/constraints/spec_delta.py` | 增量规格创建 |
| spec-archive | `reqflow/constraints/spec_archive.py` | 规格归档 |

**新增模块**：

| 模块 | 来源 | 职责 |
|------|------|------|
| guardrails.py | OpenAI Agents SDK | 并行约束验证 + 快速失败 |
| file_boundary.py | freeze (garrytan) | 文件编辑边界控制，防止子智能体越权 |
| debug_strategy.py | systematic-debugging (superpowers) | 结构化调试策略：observe→classify→hypothesize→verify→fix |

**并行 Guardrails**：

```python
async def run_with_guardrails(agent_task, constraints):
    agent_result, constraint_results = await asyncio.gather(
        agent_task,
        run_constraints(constraints)
    )
    if any_failed(constraint_results):
        return FAIL_FAST
```

---

## 4. 运行时抽象层

### 4.1 RuntimeConfig 接口

```python
@dataclass
class RuntimeConfig:
    name: str                    # "claude", "gpt", "gemini", "deepseek"
    display_name: str            # "Claude Code", "GPT-4o", "Gemini Pro"

    capabilities:
        supports_agent_tools: bool
        supports_bash: bool
        supports_file_edit: bool
        supports_image: bool
        max_context_tokens: int

    tool_mapping:
        read_file: str
        edit_file: str
        bash: str
        agent: str

    context_format:
        system_prompt_template: str
        skill_format: "markdown" | "json" | "xml"
        artifact_format: "markdown" | "json"

    paths:
        run_dir: str
        state_file: str
        log_file: str
```

### 4.2 预置运行时配置

| Runtime | 特点 |
|---------|------|
| `claude.yaml` | 完整能力，Agent 工具原生支持，markdown 格式 |
| `gpt.yaml` | 需要 function calling 适配，无原生 Agent，需外部编排 |
| `gemini.yaml` | 类似 GPT，但支持更长上下文 |
| `deepseek.yaml` | 代码能力强，但工具支持有限 |
| `manual.yaml` | 纯人工模式，所有步骤输出为 checklist |

---

## 5. 技能精简策略

### 5.1 被移除的 49 个 support 技能

| 类别 | 数量 | 处理方式 |
|------|------|----------|
| support-verification (6) | 6 | 合并入 `reqflow/tools/verify-*.py` |
| support-development (7) | 7 | 核心能力已由 orchestration 层覆盖 |
| support-infra (6) | 6 | 合并入 `reqflow/tools/infra_catalog.py` |
| support-writing (7) | 7 | 与 Java 后端交付无关 |
| support-pipeline (4) | 4 | 合并入 `reqflow/tools/deploy.py` |
| support-setup (4) | 4 | 合并入 `reqflow/context/bootstrap.py` |
| support-misc (12) | 12 | 全部移除 |
| support-domain-rules (1) | 1 | 合并入 `reqflow/context/standards.py` |

### 5.2 外部 Skill 方法论吸收

| 外部 Skill | 来源 | 安装量 | 整合方式 |
|-----------|------|--------|---------|
| systematic-debugging | superpowers | 94K | 增强 constraints/debug_strategy.py |
| test-driven-development | superpowers | 81.6K | 增强 constraints/tdd_gate.py |
| requesting-code-review | superpowers | 82.3K | 增强 evaluation/code_review.py |
| receiving-code-review | superpowers | 65.2K | 增强 evaluation/code_review.py |
| verification-before-completion | superpowers | 67.7K | 增强 evaluation/completion_gate.py |
| subagent-driven-development | superpowers | 69.7K | 增强 orchestration/agent_coordinator.py |
| dispatching-parallel-agents | superpowers | 63.1K | 新增并行调度能力 |
| writing-plans | superpowers | 93.3K | 增强 orchestration/plan_executor.py |
| executing-plans | superpowers | 75.7K | 增强 orchestration/plan_executor.py |
| code-reviewer | google-gemini | agentskill.sh | 增强 evaluation/code_review.py |
| freeze | garrytan | clawhub | 新增 constraints/file_boundary.py |

---

## 6. 最终目录结构

```
reqflow/
├── context/                      ← 01 上下文管理
│   ├── __init__.py
│   ├── bootstrap.py
│   ├── pack_builder.py
│   ├── discovery.py
│   ├── code_graph.py
│   ├── semantic_index.py
│   ├── impact.py
│   └── standards.py
│
├── tools/                        ← 02 工具系统
│   ├── __init__.py
│   ├── registry.py
│   ├── build.py
│   ├── deploy.py
│   ├── adapter_factory.py
│   ├── verify_api.py
│   ├── verify_ui.py
│   ├── verify_message.py
│   ├── verify_rpc.py
│   └── infra_catalog.py
│
├── orchestration/                ← 03 执行编排
│   ├── __init__.py
│   ├── main_flow.py
│   ├── workflow_run.py
│   ├── loop_engine.py
│   ├── agent_coordinator.py
│   ├── java_agent_coordinator.py
│   ├── router.py
│   └── plan_executor.py
│
├── state/                        ← 04 状态与记忆
│   ├── __init__.py
│   ├── session.py
│   ├── memory.py
│   ├── checkpoint.py
│   ├── evolution.py
│   ├── checklist.py
│   └── intelligence.py
│
├── evaluation/                   ← 05 评估与观测
│   ├── __init__.py
│   ├── tracer.py
│   ├── quality_gates.py
│   ├── compliance.py
│   ├── test_plan.py
│   ├── completion_gate.py
│   └── code_review.py
│
├── constraints/                  ← 06 约束与恢复
│   ├── __init__.py
│   ├── constitution.py
│   ├── design_gate.py
│   ├── tdd_gate.py
│   ├── spec_governance.py
│   ├── spec_delta.py
│   ├── spec_archive.py
│   ├── guardrails.py
│   ├── file_boundary.py
│   └── debug_strategy.py
│
├── runtime/                      ← 模型运行时抽象层
│   ├── runtime_config.py
│   ├── registry.py
│   └── providers/
│       ├── claude.yaml
│       ├── gpt.yaml
│       ├── gemini.yaml
│       ├── deepseek.yaml
│       └── manual.yaml
│
├── agents/                       ← 子智能体模板
│   ├── dev_agent.md
│   ├── verify_agent.md
│   ├── review_agent.md
│   ├── build_agent.md
│   ├── deploy_agent.md
│   └── test_plan_agent.md
│
├── scripts/                      ← 运行时脚本
│   ├── runtime_support.py
│   ├── project_scan.py
│   ├── run_checks.py
│   ├── spec_governance_runner.py
│   ├── workflow_intelligence_runner.py
│   ├── java_context_engine.py
│   ├── agent_execution_runner.py
│   ├── delivery_verification_runner.py
│   └── evolution_runner.py
│
├── templates/                    ← 产物模板
├── docs/                         ← 文档
├── commands/                     ← 命令入口
├── hooks/                        ← 钩子
├── README.md
└── CHANGELOG.md
```

---

## 7. 迁移计划

### Phase 1：骨架搭建

- 创建 `reqflow/` 6 层目录结构
- 创建 `runtime/` 运行时抽象层
- 迁移现有核心模块到对应层
- 删除 49 个 support skills
- 更新 SKILL-INDEX.md

### Phase 2：能力增强

- 下载并整合外部 skill 的方法论
- 新增 session、memory、checkpoint、tracer、guardrails 模块
- 增强并行 agent 调度和代码审查流程
- 增强调试策略

### Phase 3：运行时适配

- 实现 RuntimeConfig 接口
- 创建 claude.yaml、gpt.yaml 等 provider 配置
- 适配 commands/ 按 runtime 映射

### Phase 4：验证

- 用 Java 后端需求跑一次完整 main-flow
- 验证多 runtime 配置可用
- 更新文档

---

## 8. 风险与约束

| 风险 | 缓解措施 |
|------|---------|
| 迁移过程中 workflow 中断 | Phase 1 保持现有 workflow 可用，渐进迁移 |
| 外部 skill 方法论吸收不充分 | 先下载原文件到本地，逐个分析后再整合 |
| 多 runtime 配置复杂度高 | 先实现 claude.yaml 和 manual.yaml，其他渐进添加 |
| 并行 agent 调度引入新 bug | 保持串行为默认，并行为可选模式 |
