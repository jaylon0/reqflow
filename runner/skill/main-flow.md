---
name: main-flow
description: >
  完整 PRD-to-code 流程入口。当用户要求跑完整流程、提供 PRD、多模块变更、跨仓库任务、
  可恢复开发流程时触发。包含 10 阶段管线，支持持久化产物、checkpoint、跨会话恢复、
  模块级编码、审查和修复循环。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Agent
---

# reqflow:main-flow

完整 PRD-to-code 工作流。适用于大型需求、多模块变更、需要可恢复运行的场景。

## 触发方式

```text
/reqflow:main-flow <PRD 或需求描述>
```

或自然语言：

- "跑完整流程"
- "从 PRD 到代码走一遍"
- "完整交付这个需求"
- "可恢复的开发流程"

轻量需求请使用 `flow` skill 而非本 skill。

## 强制规则

- 在 `.dev-workflow/runs/<run-id>/` 下创建或恢复运行。
- 继续已有运行前先读取 `state.json` 和 `memory.md`。
- 不要自动切换分支。如果记录的分支与当前分支不同，展示差异并询问确认。
- 每个 checkpoint 处有未解决 BLOCKER 时必须停止。
- 失败的检查、审查发现和模块修复通过 `loop-engine` 处理。
- 每个步骤、模块、checkpoint 和循环决策后更新 `state.json`。
- 从 `planned_modules` 和 `completed_modules` 推导下一个模块，不要从文字描述推断模块顺序。
- 模块级编辑或循环前，将当前模块的授权范围写入 `state.json`。
- 秘钥不得写入运行产物。
- 持久行为变更前运行 spec governance。
- Java 后端工作在技术计划前运行上下文发现（除非 L0 分析或简单本地编辑）。
- 模块编码前、审查完成前、最终完成前运行质量门控。
- 验证通过且用户确认后才归档 spec。
- 不要自动应用 evolution proposal 中的 memory/skill/template/全局配置变更。

## 运行目录结构

每次运行在 `.dev-workflow/runs/<run-id>/` 下创建以下文件：

```text
.dev-workflow/runs/<run-id>/
├── state.json                  # 运行状态（恢复契约）
├── memory.md                   # 运行级记忆
├── 01_prd_summary.md           # PRD 理解摘要
├── 02_spec_delta.md            # Spec 变更
├── 03_workflow_intelligence.md # 工作流智能（场景、画像、清单）
├── 04_context_discovery.md     # 上下文发现（代码图、语义索引、影响分析）
├── 05_tech_plan.md             # 技术方案
├── 06_impl_plan.md             # 实现计划（含模块列表）
├── 07_agent_execution.md       # 智能体执行记录
├── 08_code_review.md           # 代码审查结果
├── 09_verification.md          # 交付验证
├── 10_archive.md               # 归档与演进
├── loops/                      # 修复循环记录
│   └── <loop-id>.md
├── graph/                      # 代码图数据
├── rag/                        # RAG 索引数据
└── agent/                      # 智能体执行产物
    ├── scenario.json
    ├── profile.json
    ├── work_items.seed.json
    ├── work_items.json
    ├── main-log.md
    ├── lessons-learned.md
    ├── compliance-report.md
    ├── evolution-report.md
    ├── context-packs/
    ├── checklists/
    └── reports/
```

## 10 阶段管线

```text
PRD → spec → intelligence → context → tech_plan → impl_plan → agent_exec → review → verify → archive
  0      1        2            3          4           5            6          7        8        9
```

### 阶段 0：启动或恢复运行

**操作：**
- 生成 run-id（格式：`YYYYMMDD-HHMMSS-<短描述>`）
- 创建 `.dev-workflow/runs/<run-id>/` 目录
- 初始化 `state.json`（使用 `templates/run-state.example.json` 模板）
- 如果是恢复运行，读取已有 `state.json` 确定断点

**state.json 关键字段：**
- `current_step`: 当前阶段（0-9）
- `planned_modules`: 从 impl_plan 复制的有序模块列表
- `completed_modules`: 已完成实现、验证和审查的模块 id
- `authorized_scope`: 当前步骤或循环允许的模块和文件
- `failure_fingerprints`: 以稳定失败指纹为 key 的重试计数
- `pending_confirmations`: 未解决的产品/API/架构/数据/provider/范围决策
- `last_stable_step` / `last_stable_artifact`: 最新可安全恢复的点
- `change_id`: 当前 spec governance 变更 id
- `spec_status`: draft | approved | archived | blocked
- `quality_gates`: 设计、TDD、审查和验证门控状态
- `archive_status`: not_started | ready | archived | blocked

### 阶段 1：PRD 理解 → `01_prd_summary.md`

**输入：** 用户提供的 PRD、issue、需求描述
**输出：** `01_prd_summary.md`

**操作：**
- 解析需求，提取功能点、非功能需求、约束条件
- 识别利益相关者和验收标准
- 标记不明确的地方为 BLOCKER

**Checkpoint：** PRD 摘要包含未解决问题时停止，等待用户补充。

### 阶段 2：Spec Governance → `02_spec_delta.md`

**输入：** `01_prd_summary.md`
**输出：** `02_spec_delta.md`

**操作：**
- 运行 `spec-governance` 和 `spec-delta` skill
- 运行 `constitution-check` 检查合规性
- 将需求映射到 spec 变更
- 对持久行为变更需要用户审批

**Checkpoint：** spec delta 变更持久行为时停止，等待审批。

### 阶段 3：Workflow Intelligence → `03_workflow_intelligence.md` + `agent/*`

**输入：** `01_prd_summary.md`, `02_spec_delta.md`
**输出：** `03_workflow_intelligence.md`, `agent/scenario.json`, `agent/profile.json`, `agent/work_items.seed.json`, `agent/checklists/`

**操作：**
- 运行 `workflow_intelligence_runner.py --run-dir <dir>` 生成基础产物
- 运行 `workflow-intelligence` skill 审查场景检测
- 场景置信度 < 0.7 时请用户确认或调整
- 审查工作项分解和清单
- 生成 compliance 和 evolution 产物

**Checkpoint：** 场景检测或画像选择有歧义时停止。

### 阶段 4：上下文发现 → `04_context_discovery.md` + `graph/` + `rag/`

**输入：** 前序产物
**输出：** `04_context_discovery.md`, `graph/`, `rag/`, `agent/context-packs/`

**操作：**
- 运行 `java-context-engine`、`java-code-graph`、`java-semantic-index`
- 运行 `java-impact-analysis` 分析变更影响
- 运行 `context-pack-builder` 构建上下文包
- 技术差距检查：流量/容量、幂等性、发布策略、稳定性、前后端边界

**知识钩子：** `java-context-engine`, `java-code-graph`, `java-semantic-index`, `java-impact-analysis`, `context-pack-builder`

### 阶段 5：技术方案 → `05_tech_plan.md`

**输入：** 前序产物
**输出：** `05_tech_plan.md`

**操作：**
- 运行 `infra-components` 和 `domain-components` skill
- 运行 `support-infra-catalog` 和 `support-domain-rules`
- 制定技术方案：架构选型、接口设计、数据模型、组件选择
- 追加技术差距检查结论

**Checkpoint：** 技术方案选择架构、接口、数据、provider 或组件行为时停止，等待确认。

### 阶段 6：实现计划 → `06_impl_plan.md` + `agent/work_items.seed.json`

**输入：** `05_tech_plan.md`
**输出：** `06_impl_plan.md`, `agent/work_items.seed.json`

**操作：**
- 将技术方案拆分为模块级实现计划
- 确定模块顺序和依赖关系
- 生成 `planned_modules` 列表写入 `state.json`
- 运行 `context-pack-builder` 为每个模块构建上下文包
- 运行 `dynamic-checklist` 生成检查清单

**Checkpoint：** 实现计划确认后继续。

### 阶段 7：智能体执行 → `07_agent_execution.md` + `agent/work_items.json`

**输入：** `06_impl_plan.md`, `agent/work_items.seed.json`
**输出：** `07_agent_execution.md`, `agent/work_items.json`, `agent/reports/`

**操作：**
1. 运行 `agent_execution_runner.py` 验证 work_items.seed.json → work_items.json
2. 加载 `agent-coordinator` skill
3. 对每个 status=pending 的工作项：
   a. 调度 dev 智能体（Agent tool, subagent_type=claude）
   b. dev 成功后并行调度 verify + review 智能体
   c. 评估结果：全部通过 → 标记 pass；任一失败 → 进入修复循环
   d. 修复：调度新 dev 智能体附带先前发现，最多 3 轮
4. 所有工作项处理完毕后：
   - 运行 `agent_execution_runner.py` 验证最终状态
   - 写入 `07_agent_execution.md` 摘要
   - 更新 `state.json.agent_execution.status`
5. 有 blocked/failed 的工作项时写入 BLOCKER

**模块级实现（无智能体时的回退）：**
1. 从 `planned_modules` 读取模块列表
2. 选取 `completed_modules` 中不存在的第一个模块 id
3. 将该模块的 authorized_scope 复制到顶层
4. 运行实现、本地验证和审查
5. 验证和审查通过后才标记模块完成
6. 需要循环时保持 `current_module`、`authorized_scope`、`current_loop_id` 更新

### 阶段 8：代码审查 → `08_code_review.md`

**输入：** `07_agent_execution.md`, `agent/reports/`
**输出：** `08_code_review.md`

**操作：**
- 汇总智能体审查结果
- 运行 `quality-gates` 和 `tdd-gate`
- 运行 `coding-standards` 检查
- 按需求匹配度和编码规范两个维度审查

### 阶段 9：交付验证 → `09_verification.md`

**输入：** 前序产物
**输出：** `09_verification.md`

**操作：**
- 运行验证 skill（API、UI、消息、RPC 等）
- 运行 `compliance-report`
- 运行 `completion-gate` 最终门控
- 验证失败时进入 `loop-engine` 修复循环

### 阶段 10：归档与演进 → `10_archive.md`

**输入：** 验证通过的全部产物
**输出：** `10_archive.md`

**操作：**
- 运行 `spec-archive` 归档 spec 变更
- 运行 `evolution-proposal` 生成演进建议
- 更新项目文档和知识库
- 生成运行总结

**Checkpoint：** 归档应用 spec 变更到项目持久 spec 前停止确认。Evolution proposal 涉及 memory/skill/template/配置变更时不要自动应用。

## 使用 Engine 执行

### 初始化

```python
from reqflow.core import Engine
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.registry import RuntimeRegistry

# 检测或指定运行时
registry = RuntimeRegistry()
config = registry.get("claude")

# 创建 Engine 实例
run_id = "20260514-143000-add-user-auth"
run_dir = f".dev-workflow/runs/{run_id}"
engine = Engine(config=config, run_dir=run_dir)
```

### 执行完整管线

```python
main_flow_steps = [
    {"name": "prd_summary",       "type": "analysis",    "output": "01_prd_summary.md"},
    {"name": "spec_delta",        "type": "governance",  "output": "02_spec_delta.md"},
    {"name": "intelligence",      "type": "intelligence","output": "03_workflow_intelligence.md"},
    {"name": "context_discovery", "type": "context",     "output": "04_context_discovery.md"},
    {"name": "tech_plan",         "type": "planning",    "output": "05_tech_plan.md"},
    {"name": "impl_plan",         "type": "planning",    "output": "06_impl_plan.md"},
    {"name": "agent_exec",        "type": "execution",   "output": "07_agent_execution.md"},
    {"name": "code_review",       "type": "review",      "output": "08_code_review.md"},
    {"name": "verification",      "type": "verification","output": "09_verification.md"},
    {"name": "archive",           "type": "archive",     "output": "10_archive.md"},
]

result = await engine.run_workflow(
    workflow_steps=main_flow_steps,
    requirement="用户提供的 PRD 或需求文本"
)
```

### 从断点恢复

```python
import json

state_path = f"{run_dir}/state.json"
with open(state_path) as f:
    state = json.load(f)

current_step = state["current_step"]
# 从 current_step 开始执行剩余步骤
remaining = main_flow_steps[current_step:]
result = await engine.run_workflow(
    workflow_steps=remaining,
    requirement=state.get("requirement", "")
)
```

### 单步执行

```python
result = await engine.run_step(
    step={"name": "tech_plan", "type": "planning", "output": "05_tech_plan.md"},
    context={
        "prd_summary": "01_prd_summary.md 的内容",
        "spec_delta": "02_spec_delta.md 的内容",
        "run_dir": run_dir,
    }
)
```

## Checkpoint 规则

以下场景必须停止等待用户确认：

1. PRD 摘要包含未解决问题
2. 场景检测或画像选择有歧义
3. Spec delta 变更持久行为
4. 技术方案选择架构/接口/data/provider/组件行为
5. 数据库/缓存/消息/契约/schema/认证/权限/外部资源变更
6. 模块完成需要人工审查
7. 归档应用 spec 变更到项目持久 spec
8. Evolution proposal 要更新 memory/context/skills/templates/guideline 文件

使用 `BLOCKER:` 标记缺失信息或待决策项。

## 状态管理

`state.json` 是恢复契约，必须在以下时机更新：

- 每个阶段完成后
- 每个模块完成后
- 每个 checkpoint 前后
- 每个循环决策后
- 进入和退出 loop-engine 时

关键状态字段的维护：

```python
# 更新当前步骤
state["current_step"] = step_index

# 标记模块完成
state["completed_modules"].append(module_id)

# 记录失败指纹
fingerprint = f"{error_type}:{file}:{line}"
state["failure_fingerprints"][fingerprint] = \
    state["failure_fingerprints"].get(fingerprint, 0) + 1

# 更新稳定点
state["last_stable_step"] = step_index
state["last_stable_artifact"] = artifact_path

# 记录待确认项
state["pending_confirmations"].append({
    "type": "architecture_decision",
    "description": "选择 Redis 还是 Memcached 作为缓存层",
    "blocking_step": 5
})
```

## 输出格式

```text
MAIN_FLOW_STATUS: initialized|in_progress|blocked|completed
RUN_ID: <run id>
CURRENT_STEP: <0-9>
CURRENT_MODULE: <当前模块或空>
ARTIFACTS:
- <产物路径>
BLOCKERS:
- <阻塞项或空>
NEXT_ACTION:
- <需要的确认、输入或命令>
```
