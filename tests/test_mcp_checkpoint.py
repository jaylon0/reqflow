"""Tests for reqflow_checkpoint MCP tool."""

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

from reqflow.runner.mcp_server import _handle_checkpoint


@pytest.fixture
def run_dir(tmp_path):
    """Create a temporary run directory with state.json."""
    state = {
        "run_id": "test-run-001",
        "current_stage": "implementation",
        "completed_modules": ["analysis"],
        "checkpoints": [
            {
                "checkpoint_id": "cp-001",
                "run_id": "test-run-001",
                "stage": "analysis",
                "timestamp": "2026-05-14T10:00:00",
            }
        ],
    }
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return str(tmp_path)


def test_checkpoint_list(run_dir):
    """Test listing checkpoints."""
    result = asyncio.run(_handle_checkpoint({"run_dir": run_dir, "action": "list"}))
    assert len(result) == 1
    assert "cp-001" in result[0].text
    assert "analysis" in result[0].text


def test_checkpoint_create(run_dir):
    """Test creating a checkpoint."""
    with patch("reqflow.core.state_manager.StateManager") as MockSM:
        mock_sm = MagicMock()
        mock_sm.create_checkpoint.return_value = MagicMock(
            checkpoint_id="cp-002",
            stage="implementation",
            timestamp="2026-05-14T11:00:00",
        )
        MockSM.return_value = mock_sm
        result = asyncio.run(_handle_checkpoint({
            "run_dir": run_dir,
            "action": "create",
            "stage": "implementation",
        }))
        assert len(result) == 1
        assert "cp-002" in result[0].text


def test_checkpoint_restore(run_dir):
    """Test restoring a checkpoint."""
    with patch("reqflow.core.state_manager.StateManager") as MockSM:
        mock_sm = MagicMock()
        mock_sm.restore_checkpoint.return_value = (
            MagicMock(current_stage="analysis"),
            {"key": "value"},
        )
        MockSM.return_value = mock_sm
        result = asyncio.run(_handle_checkpoint({
            "run_dir": run_dir,
            "action": "restore",
            "checkpoint_id": "cp-001",
        }))
        assert len(result) == 1
        assert "cp-001" in result[0].text


def test_checkpoint_missing_run_dir():
    """Test error when run_dir is missing."""
    result = asyncio.run(_handle_checkpoint({"action": "list"}))
    assert "错误" in result[0].text


def test_checkpoint_invalid_action(run_dir):
    """Test error for invalid action."""
    result = asyncio.run(_handle_checkpoint({"run_dir": run_dir, "action": "invalid"}))
    assert "错误" in result[0].text
