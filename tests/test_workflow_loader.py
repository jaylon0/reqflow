from reqflow.core.workflow_loader import WorkflowLoader
from reqflow.core.graph import Graph

def test_load_flow():
    loader = WorkflowLoader()
    stages = loader.get_stages("flow")
    assert len(stages) == 3
    assert stages[0]["name"] == "分析"
    assert stages[1]["name"] == "实现"
    assert stages[2]["name"] == "验证"

def test_load_main_flow():
    loader = WorkflowLoader()
    stages = loader.get_stages("main-flow")
    assert len(stages) == 11

def test_list_workflows():
    loader = WorkflowLoader()
    workflows = loader.list_workflows()
    assert "flow" in workflows
    assert "main-flow" in workflows

def test_load_nonexistent():
    loader = WorkflowLoader()
    try:
        loader.get_stages("nonexistent")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass

def test_get_loop_config():
    loader = WorkflowLoader()
    loop = loader.get_loop_config("main-flow")
    assert loop is not None
    assert "state_machine" in loop


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
    edge_pairs = {(e.source, e.target) for e in graph.edges}
    assert ("分析", "实现") in edge_pairs
    assert ("实现", "验证") in edge_pairs
