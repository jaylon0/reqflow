---
name: graph-flow
description: >
  图编排工作流入口。支持分支、条件路由、并行执行、human gate、loop subgraph。
  从 YAML 加载图定义或手动构建。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
---

# graph-flow

图编排工作流入口。

## 触发方式

```
/reqflow:graph-flow <工作流名称或需求>
```

## 从 YAML 加载

```python
from reqflow.core import Engine, RuntimeRegistry

registry = RuntimeRegistry()
config = registry.get("manual")
engine = Engine(config=config)

# 加载图工作流
graph = engine.workflow_loader.load_graph("graph-example")
result = await engine.run_graph(graph)
```

## 手动构建图

```python
from reqflow.core.graph import Node, Edge, Graph

nodes = {
    "analyze": Node(id="analyze", type="agent", handler=analyze_fn),
    "gate": Node(id="gate", type="decision", handler=gate_fn),
    "implement": Node(id="implement", type="agent", handler=impl_fn),
    "verify": Node(id="verify", type="agent", handler=verify_fn),
    "human_review": Node(id="human_review", type="human_gate", handler=lambda s: s),
}

edges = [
    Edge(source="analyze", target="gate"),
    Edge(source="gate", target="implement", condition=lambda s: s.get("confidence", 0) >= 0.7),
    Edge(source="gate", target="human_review", condition=lambda s: s.get("confidence", 0) < 0.7),
    Edge(source="human_review", target="implement"),
    Edge(source="implement", target="verify"),
]

graph = Graph(nodes=nodes, edges=edges, entry="analyze", exit=["verify"])
```

## Node 类型

| 类型 | 说明 | 行为 |
|------|------|------|
| agent | 调度 Agent 执行 | 调用 handler，传递 state |
| tool | 执行工具 | 调用外部工具（build, deploy 等） |
| decision | 条件路由 | 评估 condition，选择 edge |
| human_gate | 人工检查点 | 暂停执行，等待人工输入 |
| subgraph | 嵌套图 | 嵌入另一个 Graph |

## Loop Subgraph

```python
from reqflow.core.graph import LoopSubgraph

loop = LoopSubgraph(inner_graph, max_rounds=3)
result = await loop.run(state)
```

## 并行 Fan-out

当一个节点有多条无条件 edge 时，自动并行执行：
```
A → B
A → C
B → D
C → D
```
B 和 C 并行执行，都完成后进入 D。
