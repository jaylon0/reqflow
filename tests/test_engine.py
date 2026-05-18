import asyncio
import shutil

from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.adapters.api import APIAdapter
from reqflow.core.adapters.manual import ManualAdapter
from reqflow.core.graph import Graph, Node, Edge

def test_engine_selects_api_adapter_for_gpt():
    config = RuntimeConfig(
        name="gpt", display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    engine = Engine(config=config, run_dir="/tmp/test-engine-select")
    adapter = engine.select_adapter()
    assert isinstance(adapter, APIAdapter)
    assert adapter.model == "gpt-4o"
    assert adapter.base_url == "https://api.openai.com/v1"
    assert adapter.api_key == "sk-test"
    import shutil; shutil.rmtree("/tmp/test-engine-select", ignore_errors=True)

def test_engine_selects_manual_fallback():
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-engine-manual")
    adapter = engine.select_adapter()
    assert isinstance(adapter, ManualAdapter)
    import shutil; shutil.rmtree("/tmp/test-engine-manual", ignore_errors=True)

def test_engine_selects_deepseek_adapter():
    config = RuntimeConfig(
        name="deepseek", display_name="DeepSeek",
        api_key="sk-ds",
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )
    engine = Engine(config=config, run_dir="/tmp/test-engine-ds")
    adapter = engine.select_adapter()
    assert isinstance(adapter, APIAdapter)
    assert adapter.model == "deepseek-chat"
    assert adapter.provider == "deepseek"
    shutil.rmtree("/tmp/test-engine-ds", ignore_errors=True)


def test_engine_parallel_dispatch():
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-engine-parallel")

    async def mock_agent_1(prompt, **kwargs):
        await asyncio.sleep(0.1)
        return {"status": "pass", "result": "verify ok"}

    async def mock_agent_2(prompt, **kwargs):
        await asyncio.sleep(0.1)
        return {"status": "pass", "result": "review ok"}

    async def _run():
        return await engine.dispatch_parallel([
            {"name": "verify", "handler": mock_agent_1, "prompt": "verify code"},
            {"name": "review", "handler": mock_agent_2, "prompt": "review code"},
        ])

    results = asyncio.run(_run())

    assert len(results) == 2
    assert results[0]["name"] == "verify"
    assert results[0]["status"] == "pass"
    assert results[1]["name"] == "review"
    assert results[1]["status"] == "pass"

    shutil.rmtree("/tmp/test-engine-parallel", ignore_errors=True)


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

    shutil.rmtree("/tmp/test-engine-graph", ignore_errors=True)
