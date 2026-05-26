"""Tests for core.workflow_engine."""

from __future__ import annotations

import json

import pytest

from core.models import AgentRole, RunState, Stage
from core.output_validator import OutputValidator
from core.stage_executor import StageExecutor
from core.workflow_engine import RunResult, Workflow, WorkflowEngine


async def good_handler(prompt: str) -> str:
    """Handler that returns valid, high-quality output."""
    return json.dumps({
        "agent_role": "agent",
        "task": "task",
        "conclusion": "A" * 100 + " /file.py Controller def test",
        "confidence": 0.9,
        "findings": ["f1", "f2", "f3"],
        "recommendations": ["r1"],
        "risks": [],
        "skills_requested": [],
    })


def _make_workflow() -> Workflow:
    return Workflow(
        name="test-flow",
        version="1.0",
        stages=[
            Stage(
                id="analysis",
                name="分析",
                skill="analysis",
                task="分析需求",
                agents=[AgentRole(role="agent", task="任务")],
                required_skills=[],
                optional_skills=[],
                methodology_skills=[],
            ),
            Stage(
                id="planning",
                name="计划",
                skill="planning",
                task="制定计划",
                agents=[AgentRole(role="agent", task="任务")],
                required_skills=[],
                optional_skills=[],
                methodology_skills=[],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_engine_runs_all_stages():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    assert result.status == "completed"
    assert len(result.state.completed_stages) == 2


async def test_engine_tracks_state():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    state = engine.get_state(result.state.run_id)
    assert state is not None
    assert state.status == "completed"


async def test_engine_sets_current_stage():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    # After completion, current_stage should be the last stage
    assert result.state.current_stage == "planning"


async def test_engine_records_routing_level():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow(), routing_level="L2")
    assert result.state.routing_level == "L2"


# ---------------------------------------------------------------------------
# Stage execution
# ---------------------------------------------------------------------------


async def test_engine_executes_stages_sequentially():
    execution_order: list[str] = []

    async def tracking_handler(prompt: str) -> str:
        if "分析需求" in prompt:
            execution_order.append("analysis")
        elif "制定计划" in prompt:
            execution_order.append("planning")
        return await good_handler(prompt)

    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=tracking_handler),
    )
    await engine.run("测试需求", _make_workflow())
    assert execution_order == ["analysis", "planning"]


async def test_engine_includes_previous_conclusions():
    conclusions_seen: list[str] = []

    async def context_tracking_handler(prompt: str) -> str:
        conclusions_seen.append(prompt)
        return await good_handler(prompt)

    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=context_tracking_handler),
    )
    await engine.run("测试需求", _make_workflow())
    # Second stage prompt should include first stage's conclusion
    assert len(conclusions_seen) == 2
    assert "前序阶段" in conclusions_seen[1]


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


async def test_engine_handles_stage_failure():
    async def failing_handler(prompt: str) -> str:
        raise RuntimeError("Agent 崩溃")

    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=failing_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    assert result.status == "failed"
    assert result.error is not None
    assert "Agent 崩溃" in result.error


async def test_engine_stops_on_failure():
    stages_executed: list[str] = []

    async def selective_handler(prompt: str) -> str:
        if "分析需求" in prompt:
            stages_executed.append("analysis")
            return await good_handler(prompt)
        stages_executed.append("planning")
        raise RuntimeError("Second stage fails")

    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=selective_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    assert result.status == "failed"
    assert stages_executed == ["analysis", "planning"]


async def test_engine_returns_state_on_failure():
    async def failing_handler(prompt: str) -> str:
        raise RuntimeError("fail")

    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=failing_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    assert result.state is not None
    assert result.state.status == "failed"


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------


async def test_engine_saves_checkpoint(tmp_path):
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
        checkpoint_dir=tmp_path / "checkpoints",
    )
    result = await engine.run("测试需求", _make_workflow())
    assert result.status == "completed"
    assert (tmp_path / "checkpoints" / "analysis.json").exists()
    assert (tmp_path / "checkpoints" / "planning.json").exists()


async def test_engine_no_checkpoint_without_dir():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
        checkpoint_dir=None,
    )
    result = await engine.run("测试需求", _make_workflow())
    assert result.status == "completed"


# ---------------------------------------------------------------------------
# get_state
# ---------------------------------------------------------------------------


async def test_get_state_returns_none_for_unknown():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    assert engine.get_state("nonexistent") is None


async def test_get_state_returns_run_state():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    state = engine.get_state(result.state.run_id)
    assert state is not None
    assert state.run_id == result.state.run_id


# ---------------------------------------------------------------------------
# Stage attempts tracking
# ---------------------------------------------------------------------------


async def test_engine_tracks_stage_attempts():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    for s in result.state.stages:
        assert s.attempts == 1
