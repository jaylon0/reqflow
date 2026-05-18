"""Tests for reqflow_trace and reqflow_guardrails MCP tools."""

import asyncio
import json
import sys
import types
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# --- Ensure mcp mocks are in place BEFORE importing mcp_server ---
_mcp_types = types.ModuleType("mcp.types")


class _FakeTextContent:
    """Stand-in for mcp.types.TextContent when mcp is not installed."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeTool:
    """Stand-in for mcp.types.Tool when mcp is not installed."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


_mcp_types.TextContent = _FakeTextContent
_mcp_types.Tool = _FakeTool
_mcp = types.ModuleType("mcp")
_mcp.types = _mcp_types
_mcp_server_mod = types.ModuleType("mcp.server")
_mcp_server_mod.Server = MagicMock()
_mcp_server_stdio = types.ModuleType("mcp.server.stdio")
_mcp_server_stdio.stdio_server = MagicMock()

for _name, _mod in [
    ("mcp", _mcp),
    ("mcp.types", _mcp_types),
    ("mcp.server", _mcp_server_mod),
    ("mcp.server.stdio", _mcp_server_stdio),
]:
    sys.modules[_name] = _mod

# Force reload if previously loaded without mcp
if "reqflow.runner.mcp_server" in sys.modules:
    del sys.modules["reqflow.runner.mcp_server"]

from reqflow.runner.mcp_server import _handle_trace, _handle_guardrails


@pytest.fixture
def run_dir_with_trace(tmp_path):
    """Create a temporary run directory with trace data."""
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    trace_data = {
        "trace_id": "trace-001",
        "run_id": "test-run-001",
        "name": "flow",
        "start_time": "2026-05-14T10:00:00",
        "end_time": "2026-05-14T10:05:00",
        "spans": [
            {
                "span_id": "span-001",
                "name": "analysis",
                "start_time": "2026-05-14T10:00:00",
                "end_time": "2026-05-14T10:02:00",
                "duration_ms": 120000,
                "status": "success",
            }
        ],
    }
    trace_file = trace_dir / "trace-001.json"
    trace_file.write_text(json.dumps(trace_data), encoding="utf-8")
    return str(tmp_path)


def test_trace_summary(run_dir_with_trace):
    """Test trace summary."""
    result = asyncio.run(_handle_trace({"run_dir": run_dir_with_trace, "action": "summary"}))
    assert len(result) == 1
    assert "trace-001" in result[0].text


def test_trace_export(run_dir_with_trace, tmp_path):
    """Test trace export."""
    output = str(tmp_path / "exported.json")
    result = asyncio.run(_handle_trace({
        "run_dir": run_dir_with_trace,
        "action": "export",
        "output": output,
    }))
    assert len(result) == 1
    assert "已导出" in result[0].text
    assert Path(output).exists()


def test_trace_missing_run_dir():
    """Test error when run_dir is missing."""
    result = asyncio.run(_handle_trace({"action": "summary"}))
    assert "错误" in result[0].text


def test_guardrails_check():
    """Test guardrails check."""
    with patch("reqflow.core.guardrails.Guardrails") as MockG:
        mock_g = MagicMock()

        async def _fake_check(ctx):
            return []

        mock_g.check = _fake_check
        MockG.return_value = mock_g
        result = asyncio.run(_handle_guardrails({"context": {"file": "test.py"}}))
        assert len(result) == 1
