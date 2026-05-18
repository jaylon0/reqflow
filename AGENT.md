# ReqFlow V2 — Agent 平台通用指令

> 本文件供 Codex、Copilot、Cursor、Gemini CLI 等任意 Agent 平台读取。
> 平台通过 MCP server 调用 ReqFlow，或直接 import Python API。

## ReqFlow 是什么

ReqFlow 是模型无关的工作流编排引擎。它不调用外部 LLM，而是编排工作流步骤，
由当前平台的 Agent 自己执行每一步。

## MCP 工具

通过 MCP server 暴露以下工具（任意支持 MCP 的 Agent 可直接调用）：

### reqflow_run
执行工作流。
```
reqflow_run(
  requirement="为 MathExpress 添加幂运算支持",
  workflow="flow",       # flow | main-flow | graph-example
  runtime="manual"       # manual | gpt | gemini | deepseek
)
```

### reqflow_run_graph
执行图编排工作流（支持分支、并行、human gate）。
```
reqflow_run_graph(
  workflow="graph-example",
  initial_state={"confidence": 0.0}
)
```

### reqflow_session_save
保存会话上下文（跨轮次持久化）。
```
reqflow_session_save(
  session_id="my-project",
  key="requirement",
  value="添加幂运算支持"
)
```

### reqflow_session_load
加载会话上下文。
```
reqflow_session_load(session_id="my-project")
```

### reqflow_status
查询运行状态。
```
reqflow_status(run_dir=".reqflow/runs/run-abc123")
```

### reqflow_list_runtimes
列出可用 runtime。

### reqflow_dashboard
获取格式化的运行面板。
```
reqflow_dashboard(run_dir=".reqflow/runs/run-abc123")
```

## Python API

```python
from reqflow.core import Engine, RuntimeRegistry
from reqflow.core.graph import Node, Edge, Graph
from reqflow.core.session import Session

# 创建引擎
registry = RuntimeRegistry()
config = registry.get("manual")
engine = Engine(config=config, run_dir=".reqflow/runs/my-run")

# 执行线性工作流
result = await engine.run_workflow_by_name("flow", requirement="...")

# 执行图工作流
graph = engine.workflow_loader.load_graph("graph-example")
result = await engine.run_graph(graph)

# 并行 Agent 调度
results = await engine.dispatch_parallel([
    {"name": "verify", "handler": verify_fn, "prompt": "验证代码"},
    {"name": "review", "handler": review_fn, "prompt": "审查代码"},
])

# Session 持久化
session = Session(session_id="proj-1", storage_dir=".reqflow/sessions")
session.save_context("key", "value")
session.save()
```

## CLI

```bash
# 执行工作流
python3 -m reqflow.runner run "需求文本" --runtime manual --workflow flow

# 查看状态
python3 -m reqflow.runner status <run-dir>

# 列出 runtime
python3 -m reqflow.runner list-runtimes
```

## 工作流定义

工作流定义在 `reqflow/workflows/` 目录：
- `flow.yaml` — 快速 3 阶段（分析 → 实现 → 验证）
- `main-flow.yaml` — 完整 10 阶段 PRD-to-code
- `graph-example.yaml` — 图编排示例（分支 + human gate）

## 目录结构

```
reqflow/
├── core/               # 核心引擎
│   ├── engine.py       # 主引擎
│   ├── graph.py        # 图编排（Node, Edge, Graph, GraphEngine, LoopSubgraph）
│   ├── session.py      # Session 持久化
│   ├── mcp_bridge.py   # MCP 工具桥接
│   └── adapters/       # 适配器（api, claude_code, manual）
├── runner/
│   ├── cli.py          # CLI 入口
│   ├── mcp_server.py   # MCP server
│   └── dashboard.py    # 终端面板
├── skills/             # Agent skill 定义
├── workflows/          # 工作流 YAML
├── agents/             # Agent 模板
└── AGENT.md            # 本文件
```
