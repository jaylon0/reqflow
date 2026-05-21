import asyncio
import pytest
from core.tool_bridge_mcp import ToolBridgeMCP


@pytest.fixture
def bridge():
    return ToolBridgeMCP()


def test_register_and_list(bridge):
    """register a tool, list_tools returns it."""
    async def handler(**kwargs):
        return "ok"
    bridge.register("my_tool", handler)
    assert "my_tool" in bridge.list_tools()


def test_list_tools_empty(bridge):
    """empty bridge has no tools."""
    assert bridge.list_tools() == []


def test_call_registered_tool(bridge):
    """call a registered tool with arguments."""
    async def handler(name="default"):
        return f"hello {name}"
    bridge.register("greeter", handler)
    result = asyncio.run(bridge.call("greeter", {"name": "world"}))
    assert result == "hello world"


def test_call_unregistered_tool(bridge):
    """call unregistered tool raises ValueError."""
    with pytest.raises(ValueError, match="工具不存在"):
        asyncio.run(bridge.call("nonexistent", {}))


def test_register_multiple(bridge):
    """register multiple tools, all appear in list."""
    async def h1(**kw):
        return 1
    async def h2(**kw):
        return 2
    bridge.register("tool_a", h1)
    bridge.register("tool_b", h2)
    tools = bridge.list_tools()
    assert "tool_a" in tools
    assert "tool_b" in tools
    assert len(tools) == 2
