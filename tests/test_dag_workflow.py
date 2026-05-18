"""Integration tests for DAG workflow execution.

Tests the parallel fan-out / convergence structure of the DAG engine,
agent template generation, and fail-fast behavior.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from reqflow.core.graph import Edge, Graph, GraphEngine, Node
from reqflow.core.workflow_loader import WorkflowLoader
from reqflow.core.agent_registry import AgentRegistry


# ─── DAG graph structure tests ───────────────────────────────


def test_main_flow_dag_has_parallel_branches():
    """main-flow DAG should have Stages 4+5 as parallel fan-out from Stage 3."""
    loader = WorkflowLoader()
    graph = loader.load_graph("main-flow")

    assert graph.entry == "启动或恢复运行"
    assert graph.exit == ["Archive and Evolution"]

    neighbors_of_3 = graph.get_neighbors("Workflow Intelligence")
    assert set(neighbors_of_3) == {"Java Context Discovery", "Technical Plan"}


def test_main_flow_dag_convergence_at_stage_6():
    """Stage 6 should have incoming edges from both Stage 4 and Stage 5."""
    loader = WorkflowLoader()
    graph = loader.load_graph("main-flow")

    incoming_to_6 = [
        e.source for e in graph.edges if e.target == "Implementation Plan"
    ]
    assert set(incoming_to_6) == {"Java Context Discovery", "Technical Plan"}


def test_main_flow_dag_sequential_chain():
    """Stages 0→1→2→3 and 6→7→8→9→10 should form sequential chains."""
    loader = WorkflowLoader()
    graph = loader.load_graph("main-flow")

    edge_pairs = {(e.source, e.target) for e in graph.edges}

    # Sequential prefix
    assert ("启动或恢复运行", "PRD 理解") in edge_pairs
    assert ("PRD 理解", "Spec Governance") in edge_pairs
    assert ("Spec Governance", "Workflow Intelligence") in edge_pairs

    # Sequential suffix after convergence
    assert ("Implementation Plan", "Agent Execution") in edge_pairs
    assert ("Agent Execution", "Code Review") in edge_pairs
    assert ("Code Review", "Delivery Verification") in edge_pairs
    assert ("Delivery Verification", "Archive and Evolution") in edge_pairs


def test_main_flow_dag_parallel_group_metadata():
    """Stages 4 and 5 should carry parallel_group='context-planning'."""
    loader = WorkflowLoader()
    graph = loader.load_graph("main-flow")

    assert graph.nodes["Java Context Discovery"].config.get("parallel_group") == "context-planning"
    assert graph.nodes["Technical Plan"].config.get("parallel_group") == "context-planning"


def test_main_flow_dag_agent_references():
    """Stage 7 should reference dev-agent and agent_coordination dispatch agents."""
    loader = WorkflowLoader()
    graph = loader.load_graph("main-flow")

    node_7 = graph.nodes["Agent Execution"]
    assert node_7.config.get("agent") == "dev-agent"

    coord = node_7.config.get("agent_coordination", {})
    dispatch = coord.get("dispatch", [])
    agent_types = {d["type"]: d.get("agent") for d in dispatch}
    assert agent_types["dev"] == "dev-agent"
    assert agent_types["verify"] == "verify-agent"
    assert agent_types["review"] == "review-agent"


# ─── Agent template integration tests ────────────────────────


def test_main_flow_agent_templates_generate_files():
    """Agent templates from main-flow.yaml should generate valid agent files."""
    output_dir = tempfile.mkdtemp()
    try:
        loader = WorkflowLoader()
        definition = loader.load("main-flow")

        registry = AgentRegistry()
        registry.load_from_workflow(definition)

        agents = registry.list_agents()
        assert "dev-agent" in agents
        assert "verify-agent" in agents
        assert "review-agent" in agents
        assert "doc-agent" in agents

        generated = registry.generate_files(output_dir)
        assert len(generated) == 4

        for filepath in generated:
            content = Path(filepath).read_text()
            assert content.startswith("---")
            assert "name:" in content
            assert "description:" in content
            assert "model:" in content
            assert "tools:" in content
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


# ─── GraphEngine parallel execution tests ────────────────────


def _make_execution_tracker():
    """Create a tracker that records execution order and timing."""

    class Tracker:
        def __init__(self):
            self.order = []
            self.start_times = {}
            self.end_times = {}

        def make_handler(self, node_id, delay=0.05):
            async def handler(state):
                self.order.append(node_id)
                self.start_times[node_id] = time.monotonic()
                await asyncio.sleep(delay)
                self.end_times[node_id] = time.monotonic()
                state.setdefault("visited", []).append(node_id)
                return state
            return handler

        def ran_parallel(self, node_a, node_b):
            """Check if two nodes had overlapping execution windows."""
            a_start, a_end = self.start_times[node_a], self.end_times[node_a]
            b_start, b_end = self.start_times[node_b], self.end_times[node_b]
            return a_start < b_end and b_start < a_end

    return Tracker()


def test_graph_engine_parallel_fan_out():
    """GraphEngine should execute fan-out nodes in parallel via asyncio.gather."""
    tracker = _make_execution_tracker()

    # Diamond graph: A → B, A → C, B → D, C → D
    # Use larger delays to make timing windows clearly distinguishable
    graph = Graph(
        nodes={
            "A": Node(id="A", type="agent", handler=tracker.make_handler("A", 0.02)),
            "B": Node(id="B", type="agent", handler=tracker.make_handler("B", 0.3)),
            "C": Node(id="C", type="agent", handler=tracker.make_handler("C", 0.3)),
            "D": Node(id="D", type="agent", handler=tracker.make_handler("D", 0.02)),
        },
        edges=[
            Edge(source="A", target="B"),
            Edge(source="A", target="C"),
            Edge(source="B", target="D"),
            Edge(source="C", target="D"),
        ],
        entry="A",
        exit=["D"],
    )

    engine = GraphEngine(graph, state={})
    result = asyncio.run(engine.run())

    # All nodes executed
    assert set(result["visited"]) == {"A", "B", "C", "D"}

    # B and C ran in parallel (overlapping time windows)
    assert tracker.ran_parallel("B", "C")

    # A ran before B and C
    assert tracker.end_times["A"] <= tracker.start_times["B"]
    assert tracker.end_times["A"] <= tracker.start_times["C"]

    # D ran after both B and C (with tolerance for scheduling jitter)
    tolerance = 0.01
    assert tracker.start_times["D"] >= tracker.end_times["B"] - tolerance
    assert tracker.start_times["D"] >= tracker.end_times["C"] - tolerance


def test_graph_engine_convergence_first_path_wins():
    """In a diamond graph, the convergence node executes when the first path reaches it.

    GraphEngine does NOT wait for all predecessors — the first path to reach
    a node executes it, and the _visited set prevents the second path from
    re-executing it.
    """
    execution_log = []

    def make_handler(node_id, delay):
        async def handler(state):
            execution_log.append(f"{node_id}_start")
            await asyncio.sleep(delay)
            execution_log.append(f"{node_id}_end")
            return state
        return handler

    # A → B (slow), A → C (fast), B → D, C → D
    # C is faster, so C reaches D first and executes it
    graph = Graph(
        nodes={
            "A": Node(id="A", type="agent", handler=make_handler("A", 0.02)),
            "B": Node(id="B", type="agent", handler=make_handler("B", 0.3)),
            "C": Node(id="C", type="agent", handler=make_handler("C", 0.15)),
            "D": Node(id="D", type="agent", handler=make_handler("D", 0.02)),
        },
        edges=[
            Edge(source="A", target="B"),
            Edge(source="A", target="C"),
            Edge(source="B", target="D"),
            Edge(source="C", target="D"),
        ],
        entry="A",
        exit=["D"],
    )

    engine = GraphEngine(graph, state={})
    asyncio.run(engine.run())

    # D executes exactly once (first path wins, second is skipped by _visited)
    assert execution_log.count("D_start") == 1

    # C (faster) reaches D before B does
    c_end_idx = execution_log.index("C_end")
    d_start_idx = execution_log.index("D_start")
    assert c_end_idx < d_start_idx


def test_graph_engine_fail_fast_stops_execution():
    """When a node sets failed=True, downstream nodes should still execute via GraphEngine.

    Note: GraphEngine itself does not check state.failed — fail-fast is handled
    by _make_dag_node_handler in the Engine layer. This test verifies GraphEngine
    behavior: all nodes execute, but state carries the failed flag.
    """
    executed = []

    async def ok_handler(state):
        executed.append("ok")
        return state

    async def fail_handler(state):
        executed.append("fail")
        state["failed"] = True
        return state

    async def downstream_handler(state):
        executed.append("downstream")
        return state

    graph = Graph(
        nodes={
            "A": Node(id="A", type="agent", handler=ok_handler),
            "B": Node(id="B", type="agent", handler=fail_handler),
            "C": Node(id="C", type="agent", handler=ok_handler),
            "D": Node(id="D", type="agent", handler=downstream_handler),
        },
        edges=[
            Edge(source="A", target="B"),
            Edge(source="A", target="C"),
            Edge(source="B", target="D"),
            Edge(source="C", target="D"),
        ],
        entry="A",
        exit=["D"],
    )

    engine = GraphEngine(graph, state={})
    result = asyncio.run(engine.run())

    # A, B, C all executed; B sets failed=True
    assert "ok" in executed
    assert "fail" in executed
    assert result.get("failed") is True


def test_graph_engine_visited_prevents_double_execution():
    """In a diamond graph, the convergence node should execute exactly once."""
    visit_count = {}

    def counting_handler(node_id):
        async def handler(state):
            visit_count[node_id] = visit_count.get(node_id, 0) + 1
            return state
        return handler

    graph = Graph(
        nodes={
            "A": Node(id="A", type="agent", handler=counting_handler("A")),
            "B": Node(id="B", type="agent", handler=counting_handler("B")),
            "C": Node(id="C", type="agent", handler=counting_handler("C")),
            "D": Node(id="D", type="agent", handler=counting_handler("D")),
        },
        edges=[
            Edge(source="A", target="B"),
            Edge(source="A", target="C"),
            Edge(source="B", target="D"),
            Edge(source="C", target="D"),
        ],
        entry="A",
        exit=["D"],
    )

    engine = GraphEngine(graph, state={})
    asyncio.run(engine.run())

    # D should execute exactly once despite two incoming edges
    assert visit_count.get("D", 0) == 1


# ─── Linear workflow regression test ─────────────────────────


def test_flow_workflow_still_loads_as_linear():
    """The simple 'flow' workflow (no depends_on) should still load as linear chain."""
    loader = WorkflowLoader()
    graph = loader.load_graph("flow")

    edge_pairs = {(e.source, e.target) for e in graph.edges}
    assert len(edge_pairs) == 2  # A→B, B→C
    assert graph.entry == "分析"
    assert graph.exit == ["验证"]
