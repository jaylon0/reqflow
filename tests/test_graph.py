import asyncio

from reqflow.core.graph import Node, Edge, Graph, GraphEngine, LoopSubgraph

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


def test_graph_engine_linear():
    """Engine traverses a linear graph A->B->C."""
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

    engine_b = GraphEngine(graph, state={"go": True})
    result_b = asyncio.run(engine_b.run())
    assert result_b["chosen"] == "b"

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

    result1 = asyncio.run(engine.run())
    assert result1.get("a_done") is True
    assert result1.get("b_done") is None
    assert result1.get("_paused_at") == "gate"

    result2 = asyncio.run(engine.run_from("gate"))
    assert result2.get("b_done") is True
    assert result2.get("_status") == "completed"


def test_loop_subgraph_basic():
    """Loop subgraph executes until condition met."""
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
    assert state["r"] == 3
