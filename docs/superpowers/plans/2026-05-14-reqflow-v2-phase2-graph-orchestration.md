# ReqFlow V2 Phase 2: Graph Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace linear workflow execution with a directed graph engine supporting branching, conditional edges, parallel fan-out/fan-in, and loop-as-subgraph patterns.

**Architecture:** New `core/graph.py` defines Node/Edge/Graph dataclasses and a GraphEngine executor. WorkflowLoader gains graph YAML parsing with backward-compatible stages→graph conversion. Loop engine becomes a reusable subgraph pattern.

**Tech Stack:** Python 3.10+, asyncio, pytest

---

## File Structure

```
reqflow/
├── core/
│   ├── graph.py              # CREATE: Node, Edge, Graph, GraphEngine
│   ├── workflow_loader.py    # MODIFY: add graph YAML parsing + stages→graph conversion
│   └── engine.py             # MODIFY: integrate GraphEngine for graph workflows
├── workflows/
│   └── graph-example.yaml    # CREATE: example graph workflow
└── tests/
    ├── test_graph.py         # CREATE: graph engine tests
    └── test_workflow_loader.py # MODIFY: add graph loading tests
```

---

### Task 1: Graph data structures

**Files:**
- Create: `reqflow/core/graph.py`
- Test: `reqflow/tests/test_graph.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_graph.py
from reqflow.core.graph import Node, Edge, Graph

def test_node_creation():
    node = Node(id="analyze", type="agent", handler=lambda s: s)
    assert node.id == "analyze"
    assert node.type == "agent"
    assert node.config == {}

def test_edge_unconditional():
    edge = Edge(source="a", target="b")
    assert edge.source == "a"
    assert edge.target == "b"
    assert edge.condition is None

def test_edge_conditional():
    def check(s): return s.get("score", 0) > 0.5
    edge = Edge(source="a", target="b", condition=check)
    assert edge.condition({"score": 0.8}) is True
    assert edge.condition({"score": 0.3}) is False

def test_graph_creation():
    nodes = {
        "a": Node(id="a", type="agent", handler=lambda s: s),
        "b": Node(id="b", type="tool", handler=lambda s: s),
    }
    edges = [Edge(source="a", target="b")]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["b"])
    assert graph.entry == "a"
    assert graph.exit == ["b"]
    assert len(graph.edges) == 1

def test_graph_neighbors():
    nodes = {
        "a": Node(id="a", type="agent", handler=lambda s: s),
        "b": Node(id="b", type="tool", handler=lambda s: s),
        "c": Node(id="c", type="tool", handler=lambda s: s),
    }
    edges = [
        Edge(source="a", target="b"),
        Edge(source="a", target="c"),
    ]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["b", "c"])
    neighbors = graph.get_neighbors("a")
    assert set(neighbors) == {"b", "c"}

def test_graph_neighbors_conditional():
    nodes = {
        "a": Node(id="a", type="decision", handler=lambda s: s),
        "b": Node(id="b", type="agent", handler=lambda s: s),
        "c": Node(id="c", type="agent", handler=lambda s: s),
    }
    edges = [
        Edge(source="a", target="b", condition=lambda s: s.get("go")),
        Edge(source="a", target="c", condition=lambda s: not s.get("go")),
    ]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["b", "c"])
    neighbors_b = graph.get_neighbors("a", state={"go": True})
    assert neighbors_b == ["b"]
    neighbors_c = graph.get_neighbors("a", state={"go": False})
    assert neighbors_c == ["c"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_graph.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'reqflow.core.graph'`

- [ ] **Step 3: Implement graph data structures**

```python
# reqflow/core/graph.py
"""Graph data structures for workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal


@dataclass
class Node:
    """A node in the workflow graph."""
    id: str
    type: Literal["agent", "tool", "decision", "human_gate", "subgraph"]
    handler: Callable  # function or agent reference
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """A directed edge between two nodes, optionally conditional."""
    source: str  # node id
    target: str  # node id
    condition: Callable[[dict[str, Any]], bool] | None = None  # None = unconditional


@dataclass
class Graph:
    """A directed graph of workflow nodes."""
    nodes: dict[str, Node]
    edges: list[Edge]
    entry: str  # entry node id
    exit: list[str]  # terminal node ids

    def get_neighbors(
        self, node_id: str, state: dict[str, Any] | None = None
    ) -> list[str]:
        """Get target node IDs reachable from node_id.

        For unconditional edges, always included.
        For conditional edges, only included if condition(state) is True.

        Args:
            node_id: Source node ID.
            state: Current workflow state for evaluating conditions.

        Returns:
            List of reachable target node IDs.
        """
        neighbors: list[str] = []
        for edge in self.edges:
            if edge.source != node_id:
                continue
            if edge.condition is None:
                neighbors.append(edge.target)
            elif state is not None and edge.condition(state):
                neighbors.append(edge.target)
        return neighbors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/graph.py reqflow/tests/test_graph.py
git commit -m "feat: add Graph data structures (Node, Edge, Graph)"
```

---

### Task 2: GraphEngine execution

**Files:**
- Modify: `reqflow/core/graph.py`
- Test: `reqflow/tests/test_graph.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_graph.py — add at end
import asyncio
from reqflow.core.graph import Node, Edge, Graph, GraphEngine

def test_graph_engine_linear():
    """Engine traverses a linear graph A→B→C."""
    call_order = []
    def make_handler(name):
        def h(state):
            call_order.append(name)
            return state
        return h

    nodes = {
        "a": Node(id="a", type="agent", handler=make_handler("a")),
        "b": Node(id="b", type="agent", handler=make_handler("b")),
        "c": Node(id="c", type="agent", handler=make_handler("c")),
    }
    edges = [Edge(source="a", target="b"), Edge(source="b", target="c")]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["c"])
    engine = GraphEngine(graph, state={})
    result_state = asyncio.run(engine.run())
    assert call_order == ["a", "b", "c"]
    assert result_state["_status"] == "completed"

def test_graph_engine_branching():
    """Engine follows conditional branch."""
    def go_handler(state):
        state["chosen"] = "b"
        return state
    def skip_handler(state):
        state["chosen"] = "c"
        return state

    nodes = {
        "a": Node(id="a", type="decision", handler=lambda s: s),
        "b": Node(id="b", type="agent", handler=go_handler),
        "c": Node(id="c", type="agent", handler=skip_handler),
    }
    edges = [
        Edge(source="a", target="b", condition=lambda s: s.get("go")),
        Edge(source="a", target="c", condition=lambda s: not s.get("go")),
    ]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["b", "c"])

    # Test branch to b
    engine_b = GraphEngine(graph, state={"go": True})
    result_b = asyncio.run(engine_b.run())
    assert result_b["chosen"] == "b"

    # Test branch to c
    engine_c = GraphEngine(graph, state={"go": False})
    result_c = asyncio.run(engine_c.run())
    assert result_c["chosen"] == "c"

def test_graph_engine_parallel_fan_out():
    """Engine dispatches parallel fan-out from a node."""
    nodes = {
        "a": Node(id="a", type="agent", handler=lambda s: s),
        "b": Node(id="b", type="agent", handler=lambda s: {**s, "b_done": True}),
        "c": Node(id="c", type="agent", handler=lambda s: {**s, "c_done": True}),
        "d": Node(id="d", type="agent", handler=lambda s: s),
    }
    edges = [
        Edge(source="a", target="b"),
        Edge(source="a", target="c"),
        Edge(source="b", target="d"),
        Edge(source="c", target="d"),
    ]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["d"])
    engine = GraphEngine(graph, state={})
    result = asyncio.run(engine.run())
    assert result.get("b_done") is True
    assert result.get("c_done") is True

def test_graph_engine_human_gate():
    """Engine pauses at human_gate and resumes from checkpoint."""
    nodes = {
        "a": Node(id="a", type="agent", handler=lambda s: {**s, "a_done": True}),
        "gate": Node(id="gate", type="human_gate", handler=lambda s: s),
        "b": Node(id="b", type="agent", handler=lambda s: {**s, "b_done": True}),
    }
    edges = [Edge(source="a", target="gate"), Edge(source="gate", target="b")]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["b"])
    engine = GraphEngine(graph, state={})

    # First run should stop at human_gate
    result1 = asyncio.run(engine.run())
    assert result1.get("a_done") is True
    assert result1.get("b_done") is None
    assert result1.get("_paused_at") == "gate"

    # Resume from gate
    result2 = asyncio.run(engine.run_from("gate"))
    assert result2.get("b_done") is True
    assert result2.get("_status") == "completed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_graph.py -v`
Expected: FAIL with `ImportError: cannot import name 'GraphEngine'`

- [ ] **Step 3: Implement GraphEngine**

Add to `reqflow/core/graph.py`:

```python
class GraphEngine:
    """Executes a workflow graph from entry to exit."""

    def __init__(self, graph: Graph, state: dict[str, Any] | None = None):
        self.graph = graph
        self.state: dict[str, Any] = state if state is not None else {}
        self._visited: set[str] = set()

    async def run(self) -> dict[str, Any]:
        """Execute graph from entry node to exit nodes."""
        return await self.run_from(self.graph.entry)

    async def run_from(self, node_id: str) -> dict[str, Any]:
        """Resume execution from a specific node."""
        self._visited.clear()
        await self._execute_node(node_id)
        if "_status" not in self.state:
            self.state["_status"] = "completed"
        return self.state

    async def _execute_node(self, node_id: str) -> None:
        """Recursively execute a node and its successors."""
        if node_id in self._visited:
            return
        self._visited.add(node_id)

        node = self.graph.nodes[node_id]

        # Execute node handler
        if asyncio.iscoroutinefunction(node.handler):
            self.state = await node.handler(self.state)
        else:
            self.state = node.handler(self.state)

        # Human gate: pause execution
        if node.type == "human_gate":
            self.state["_paused_at"] = node_id
            self.state["_status"] = "paused"
            return

        # Find and execute neighbors
        neighbors = self.graph.get_neighbors(node_id, state=self.state)

        if not neighbors:
            # Terminal node
            if node_id in self.graph.exit:
                return
            return

        # Fan-out: execute neighbors (parallel for independent branches)
        if len(neighbors) > 1:
            await asyncio.gather(*[self._execute_node(n) for n in neighbors])
        else:
            await self._execute_node(neighbors[0])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/graph.py reqflow/tests/test_graph.py
git commit -m "feat: add GraphEngine with branching, parallel fan-out, human gate"
```

---

### Task 3: WorkflowLoader graph YAML support

**Files:**
- Modify: `reqflow/core/workflow_loader.py`
- Test: `reqflow/tests/test_workflow_loader.py`
- Create: `reqflow/workflows/graph-example.yaml`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_workflow_loader.py — add at end
from reqflow.core.graph import Graph

def test_load_graph_workflow():
    loader = WorkflowLoader()
    graph = loader.load_graph("graph-example")
    assert isinstance(graph, Graph)
    assert graph.entry == "analyze"
    assert "analyze" in graph.nodes
    assert len(graph.edges) > 0

def test_stages_to_graph_conversion():
    """Existing stages format auto-converts to graph."""
    loader = WorkflowLoader()
    graph = loader.load_graph("flow")
    assert isinstance(graph, Graph)
    assert graph.entry == "分析"
    assert graph.exit == ["验证"]
    # Should have edges: 分析→实现, 实现→验证
    edge_pairs = {(e.source, e.target) for e in graph.edges}
    assert ("分析", "实现") in edge_pairs
    assert ("实现", "验证") in edge_pairs
```

- [ ] **Step 2: Create example graph workflow YAML**

```yaml
# reqflow/workflows/graph-example.yaml
name: "graph-example"
description: "Example graph workflow with branching"

graph:
  entry: "analyze"
  nodes:
    - id: "analyze"
      type: "agent"
      agent: "intelligence-agent"
      prompt: "分析需求，输出置信度分数"
      output: "confidence"

    - id: "gate"
      type: "decision"
      condition: "state.get('confidence', 0) >= 0.7"
      edges:
        - target: "implement"
          when: "true"
        - target: "clarify"
          when: "false"

    - id: "clarify"
      type: "human_gate"
      prompt: "置信度不足，请确认需求"

    - id: "implement"
      type: "agent"
      agent: "dev-agent"
      prompt: "实现需求代码"

    - id: "verify"
      type: "agent"
      agent: "verify-agent"
      prompt: "验证实现"

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

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_workflow_loader.py::test_load_graph_workflow reqflow/tests/test_workflow_loader.py::test_stages_to_graph_conversion -v`
Expected: FAIL

- [ ] **Step 4: Implement graph loading in WorkflowLoader**

Add to `reqflow/core/workflow_loader.py`:

```python
def load_graph(self, name: str) -> "Graph":
    """Load a workflow as a Graph.

    Supports two formats:
    1. Explicit 'graph' key with nodes/edges
    2. Legacy 'stages' key auto-converted to linear graph

    Args:
        name: Workflow name

    Returns:
        Graph instance ready for GraphEngine
    """
    from .graph import Node, Edge, Graph

    definition = self.load(name)

    if "graph" in definition:
        return self._parse_graph(definition["graph"])
    elif "stages" in definition:
        return self._stages_to_graph(definition["stages"])
    else:
        raise ValueError(f"Workflow '{name}' has neither 'graph' nor 'stages' key")

def _parse_graph(self, graph_def: dict) -> "Graph":
    """Parse an explicit graph definition."""
    from .graph import Node, Edge, Graph

    nodes: dict[str, Node] = {}
    for node_def in graph_def.get("nodes", []):
        node = Node(
            id=node_def["id"],
            type=node_def.get("type", "agent"),
            handler=node_def.get("handler", lambda s: s),
            config={k: v for k, v in node_def.items() if k not in ("id", "type", "handler")},
        )
        nodes[node.id] = node

    edges: list[Edge] = []
    for edge_def in graph_def.get("edges", []):
        condition = None
        cond_str = edge_def.get("condition")
        if cond_str:
            # Simple condition evaluation: "state.get('key') >= value"
            def make_condition(expr):
                def check(state):
                    try:
                        return eval(expr, {"state": state, "__builtins__": {}})
                    except Exception:
                        return False
                check.__doc__ = expr
                return check
            condition = make_condition(cond_str)

        edges.append(Edge(
            source=edge_def["source"],
            target=edge_def["target"],
            condition=condition,
        ))

    return Graph(
        nodes=nodes,
        edges=edges,
        entry=graph_def.get("entry", ""),
        exit=graph_def.get("exit", []),
    )

def _stages_to_graph(self, stages: list[dict]) -> "Graph":
    """Convert linear stages list to a Graph."""
    from .graph import Node, Edge, Graph

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    for i, stage in enumerate(stages):
        step = self._convert_stage(stage)
        node = Node(
            id=step["name"],
            type="agent",
            handler=step.get("handler", lambda s: s),
            config=step,
        )
        nodes[node.id] = node

        if i > 0:
            prev_name = self._convert_stage(stages[i - 1])["name"]
            edges.append(Edge(source=prev_name, target=node.id))

    entry = self._convert_stage(stages[0])["name"] if stages else ""
    exit_nodes = [self._convert_stage(stages[-1])["name"]] if stages else []

    return Graph(nodes=nodes, edges=edges, entry=entry, exit=exit_nodes)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_workflow_loader.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add reqflow/core/workflow_loader.py reqflow/workflows/graph-example.yaml reqflow/tests/test_workflow_loader.py
git commit -m "feat: WorkflowLoader supports graph YAML and stages→graph conversion"
```

---

### Task 4: Loop engine as subgraph

**Files:**
- Modify: `reqflow/core/graph.py`
- Modify: `reqflow/core/engine.py`
- Test: `reqflow/tests/test_graph.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_graph.py — add at end
from reqflow.core.graph import Node, Edge, Graph, GraphEngine, LoopSubgraph

def test_loop_subgraph_basic():
    """Loop subgraph executes max_rounds times."""
    round_count = {"n": 0}

    def counter(state):
        round_count["n"] += 1
        state["rounds"] = round_count["n"]
        return state

    def should_continue(state):
        return state.get("rounds", 0) < 3

    nodes = {
        "work": Node(id="work", type="agent", handler=counter),
        "check": Node(id="check", type="decision", handler=lambda s: s),
    }
    edges = [
        Edge(source="work", target="check"),
        Edge(source="check", target="work", condition=should_continue),
    ]
    inner_graph = Graph(nodes=nodes, edges=edges, entry="work", exit=["check"])

    loop = LoopSubgraph(inner_graph, max_rounds=5)
    state = asyncio.run(loop.run({}))
    assert state["rounds"] == 3
    assert state["_loop_completed"] is True

def test_loop_subgraph_max_rounds():
    """Loop respects max_rounds limit."""
    def always_continue(state):
        return True

    nodes = {
        "work": Node(id="work", type="agent", handler=lambda s: {**s, "r": s.get("r", 0) + 1}),
        "check": Node(id="check", type="decision", handler=lambda s: s),
    }
    edges = [
        Edge(source="work", target="check"),
        Edge(source="check", target="work", condition=always_continue),
    ]
    inner_graph = Graph(nodes=nodes, edges=edges, entry="work", exit=["check"])

    loop = LoopSubgraph(inner_graph, max_rounds=3)
    state = asyncio.run(loop.run({}))
    assert state["r"] == 3  # hit max_rounds
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_graph.py::test_loop_subgraph_basic reqflow/tests/test_graph.py::test_loop_subgraph_max_rounds -v`
Expected: FAIL with `ImportError: cannot import name 'LoopSubgraph'`

- [ ] **Step 3: Implement LoopSubgraph**

Add to `reqflow/core/graph.py`:

```python
class LoopSubgraph:
    """A subgraph that repeats until a condition is met or max_rounds is reached."""

    def __init__(self, graph: Graph, max_rounds: int = 3):
        self.graph = graph
        self.max_rounds = max_rounds

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the loop subgraph."""
        for round_num in range(self.max_rounds):
            state["_loop_round"] = round_num
            engine = GraphEngine(self.graph, state=state)
            state = await engine.run()

            # Check if decision node says to stop
            if state.get("_status") == "loop_break":
                break

            # Check if there's no path forward (exit reached)
            if state.get("_status") == "completed":
                break

        state["_loop_completed"] = True
        state.pop("_loop_round", None)
        state.pop("_paused_at", None)
        state["_status"] = "completed"
        return state
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/graph.py reqflow/tests/test_graph.py
git commit -m "feat: add LoopSubgraph for loop-as-subgraph pattern"
```

---

### Task 5: Integrate GraphEngine into Engine

**Files:**
- Modify: `reqflow/core/engine.py`
- Test: `reqflow/tests/test_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_engine.py — add at end
from reqflow.core.graph import Graph, Node, Edge

def test_engine_run_graph():
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-engine-graph")

    call_order = []
    def make_handler(name):
        def h(state):
            call_order.append(name)
            return state
        return h

    nodes = {
        "a": Node(id="a", type="agent", handler=make_handler("a")),
        "b": Node(id="b", type="agent", handler=make_handler("b")),
    }
    edges = [Edge(source="a", target="b")]
    graph = Graph(nodes=nodes, edges=edges, entry="a", exit=["b"])

    result = asyncio.run(engine.run_graph(graph))
    assert call_order == ["a", "b"]
    assert result["_status"] == "completed"

    import shutil
    shutil.rmtree("/tmp/test-engine-graph", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_engine.py::test_engine_run_graph -v`
Expected: FAIL with `AttributeError: 'Engine' object has no attribute 'run_graph'`

- [ ] **Step 3: Add run_graph method to Engine**

Add to `reqflow/core/engine.py` after `run_workflow_by_name`:

```python
async def run_graph(self, graph: "Graph") -> dict[str, Any]:
    """Execute a workflow graph.

    Args:
        graph: Graph instance to execute.

    Returns:
        Final state dict with _status key.
    """
    from .graph import GraphEngine

    self.state_manager.update_stage("graph_start")
    self.state_manager.save_state()

    state: dict[str, Any] = {"requirement": ""}
    graph_engine = GraphEngine(graph, state=state)
    result = await graph_engine.run()

    self.state_manager.state.agent_execution_log.append({
        "workflow": "run_graph",
        "result": result.get("_status", "unknown"),
        "timestamp": datetime.now().isoformat(),
    })
    self.state_manager.save_state()

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_engine.py::test_engine_run_graph -v`
Expected: PASS

- [ ] **Step 5: Run all tests to verify no regression**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/ -v --ignore=reqflow/tests/integration`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add reqflow/core/engine.py reqflow/tests/test_engine.py
git commit -m "feat: Engine.run_graph integrates GraphEngine for graph workflows"
```
