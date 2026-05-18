"""Tests for reqflow_parallel MCP tool."""

import asyncio
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock mcp package before importing mcp_server
mock_mcp = types.ModuleType("mcp")
mock_mcp_types = types.ModuleType("mcp.types")
mock_mcp_types.TextContent = type("TextContent", (), {"__init__": lambda self, **kw: setattr(self, '__dict__', kw)})
mock_mcp_types.Tool = type("Tool", (), {"__init__": lambda self, **kw: setattr(self, '__dict__', kw)})
mock_mcp_server = types.ModuleType("mcp.server")
mock_mcp_server.Server = MagicMock
mock_mcp_stdio = types.ModuleType("mcp.server.stdio")
mock_mcp_stdio.stdio_server = MagicMock
sys.modules.setdefault("mcp", mock_mcp)
sys.modules.setdefault("mcp.types", mock_mcp_types)
sys.modules.setdefault("mcp.server", mock_mcp_server)
sys.modules.setdefault("mcp.server.stdio", mock_mcp_stdio)

# Force reload if previously loaded without mcp
if "reqflow.runner.mcp_server" in sys.modules:
    del sys.modules["reqflow.runner.mcp_server"]

from reqflow.runner.mcp_server import _handle_parallel


def test_parallel_dispatch():
    """Test parallel agent dispatch."""
    agents = [
        {"name": "agent-1", "prompt": "task 1"},
        {"name": "agent-2", "prompt": "task 2"},
    ]
    result = asyncio.run(_handle_parallel({"agents": agents}))
    assert len(result) == 1
    assert "agent-1" in result[0].text
    assert "agent-2" in result[0].text
    assert "并行执行完成" in result[0].text


def test_parallel_empty_agents():
    """Test error when agents list is empty."""
    result = asyncio.run(_handle_parallel({"agents": []}))
    assert "错误" in result[0].text


def test_parallel_missing_agents():
    """Test error when agents parameter is missing."""
    result = asyncio.run(_handle_parallel({}))
    assert "错误" in result[0].text


def test_parallel_max_concurrent():
    """Test custom max_concurrent parameter."""
    agents = [
        {"name": "agent-1", "prompt": "task 1"},
        {"name": "agent-2", "prompt": "task 2"},
        {"name": "agent-3", "prompt": "task 3"},
    ]
    result = asyncio.run(_handle_parallel({"agents": agents, "max_concurrent": 2}))
    assert len(result) == 1
    assert "3 个 agent" in result[0].text
    assert "agent-1" in result[0].text
    assert "agent-2" in result[0].text
    assert "agent-3" in result[0].text


def test_parallel_single_agent():
    """Test with a single agent."""
    agents = [{"name": "solo", "prompt": "do something"}]
    result = asyncio.run(_handle_parallel({"agents": agents}))
    assert len(result) == 1
    assert "solo" in result[0].text
    assert "1 个 agent" in result[0].text
    assert "[OK]" in result[0].text


def test_parallel_agent_missing_name():
    """Test agent without name defaults to unnamed."""
    agents = [{"prompt": "task without name"}]
    result = asyncio.run(_handle_parallel({"agents": agents}))
    assert len(result) == 1
    assert "unnamed" in result[0].text
