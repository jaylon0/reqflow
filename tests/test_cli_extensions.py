"""Tests for CLI extensions: run-graph, checkpoint, trace."""

import asyncio
import json
import argparse
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from reqflow.runner.cli import (
    _handle_checkpoint_cmd,
    _handle_trace_cmd,
    _handle_run_graph_cmd,
)


@pytest.fixture
def run_dir(tmp_path):
    """Create a temporary run directory."""
    state = {
        "run_id": "test-run-001",
        "current_stage": "implementation",
        "checkpoints": [
            {"checkpoint_id": "cp-001", "stage": "analysis", "timestamp": "2026-05-14T10:00:00"}
        ],
    }
    (tmp_path / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return str(tmp_path)


def test_checkpoint_list(run_dir, capsys):
    """Test checkpoint list command."""
    args = MagicMock()
    args.run_dir = run_dir
    args.checkpoint_action = "list"
    _handle_checkpoint_cmd(args)
    captured = capsys.readouterr()
    assert "cp-001" in captured.out


def test_trace_summary(run_dir, capsys):
    """Test trace summary command."""
    # Create trace directory
    trace_dir = Path(run_dir) / "traces"
    trace_dir.mkdir()
    trace_data = {"trace_id": "t-001", "name": "flow", "spans": []}
    (trace_dir / "t-001.json").write_text(json.dumps(trace_data))

    args = MagicMock()
    args.run_dir = run_dir
    args.trace_action = "summary"
    _handle_trace_cmd(args)
    captured = capsys.readouterr()
    assert "t-001" in captured.out


def test_checkpoint_missing_run_dir(capsys):
    """Test error when run_dir is missing."""
    args = MagicMock()
    args.run_dir = "/nonexistent"
    args.checkpoint_action = "list"
    with pytest.raises(SystemExit):
        _handle_checkpoint_cmd(args)
    captured = capsys.readouterr()
    assert "错误" in captured.err
