"""Tests for core.checkpoint_manager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.checkpoint_manager import CheckpointManager
from core.models import (
    RunState,
    StageAnalysis,
    StageOutput,
    StageState,
)


@pytest.fixture
def checkpoint_dir(tmp_path):
    return tmp_path / "run"


@pytest.fixture
def manager(checkpoint_dir):
    return CheckpointManager(checkpoint_dir)


def _make_output(stage_id: str = "analysis") -> StageOutput:
    return StageOutput(
        stage_id=stage_id,
        status="completed",
        analysis=StageAnalysis(
            summary="A" * 120,
            findings=["f1", "f2", "f3"],
        ),
    )


def _make_state() -> RunState:
    return RunState(
        run_id="test-001",
        requirement="test requirement",
        routing_level="L3",
        stages=[
            StageState(stage_id="analysis", status="completed"),
            StageState(stage_id="planning", status="pending"),
        ],
    )


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_save_creates_checkpoint_file(manager, checkpoint_dir):
    output = _make_output()
    state = _make_state()
    manager.save("analysis", output, state)

    path = checkpoint_dir / "checkpoints" / "analysis.json"
    assert path.exists()


def test_save_contains_correct_data(manager, checkpoint_dir):
    output = _make_output()
    state = _make_state()
    manager.save("analysis", output, state)

    path = checkpoint_dir / "checkpoints" / "analysis.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["stage_id"] == "analysis"
    assert "timestamp" in data
    assert data["output"]["stage_id"] == "analysis"
    assert data["state"]["run_id"] == "test-001"


def test_save_overwrites_existing(manager, checkpoint_dir):
    output1 = _make_output("analysis")
    output1.analysis.summary = "First version"
    state = _make_state()

    manager.save("analysis", output1, state)

    output2 = _make_output("analysis")
    output2.analysis.summary = "Second version"
    manager.save("analysis", output2, state)

    path = checkpoint_dir / "checkpoints" / "analysis.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["output"]["analysis"]["summary"] == "Second version"


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------


def test_restore_returns_output_and_state(manager):
    output = _make_output()
    state = _make_state()
    manager.save("analysis", output, state)

    result = manager.restore("analysis")
    assert result is not None

    output_dict, state_dict = result
    assert output_dict["stage_id"] == "analysis"
    assert state_dict["run_id"] == "test-001"


def test_restore_returns_none_for_missing(manager):
    result = manager.restore("nonexistent")
    assert result is None


def test_round_trip_preserves_data(manager):
    output = _make_output("planning")
    output.analysis.findings = ["alpha", "beta", "gamma"]
    state = _make_state()

    manager.save("planning", output, state)
    output_dict, state_dict = manager.restore("planning")

    assert output_dict["analysis"]["findings"] == ["alpha", "beta", "gamma"]
    assert state_dict["requirement"] == "test requirement"


# ---------------------------------------------------------------------------
# list_checkpoints
# ---------------------------------------------------------------------------


def test_list_empty(manager):
    assert manager.list_checkpoints() == []


def test_list_after_save(manager):
    output = _make_output()
    state = _make_state()

    manager.save("analysis", output, state)
    manager.save("planning", output, state)

    checkpoints = manager.list_checkpoints()
    assert "analysis" in checkpoints
    assert "planning" in checkpoints


def test_list_sorted(manager):
    output = _make_output()
    state = _make_state()

    # Save in reverse order
    manager.save("z-stage", output, state)
    manager.save("a-stage", output, state)

    checkpoints = manager.list_checkpoints()
    assert checkpoints == ["a-stage", "z-stage"]


# ---------------------------------------------------------------------------
# get_resume_point
# ---------------------------------------------------------------------------


def test_resume_point_empty(manager):
    assert manager.get_resume_point() is None


def test_resume_point_returns_latest(manager):
    output = _make_output()
    state = _make_state()

    manager.save("analysis", output, state)
    manager.save("planning", output, state)

    assert manager.get_resume_point() == "planning"


def test_resume_point_single(manager):
    output = _make_output()
    state = _make_state()

    manager.save("analysis", output, state)
    assert manager.get_resume_point() == "analysis"
