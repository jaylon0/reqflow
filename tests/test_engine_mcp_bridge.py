"""Tests for core.engine_mcp_bridge."""

from __future__ import annotations

import json

import pytest

from core.engine_mcp_bridge import EngineMCPBridge
from core.models import AgentRole, Stage
from core.stage_executor import StageExecutor
from core.workflow_engine import Workflow, WorkflowEngine


async def good_handler(prompt: str) -> str:
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
                id="s1", name="S1", skill="s1", task="t1",
                agents=[AgentRole(role="a", task="t")],
                required_skills=[], optional_skills=[], methodology_skills=[],
            ),
        ],
    )


@pytest.fixture
async def engine_and_bridge():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("测试需求", _make_workflow())
    bridge = EngineMCPBridge(engine)
    return engine, bridge, result


# ---------------------------------------------------------------------------
# handle_status
# ---------------------------------------------------------------------------


async def test_status_returns_run_info(engine_and_bridge):
    _, bridge, result = engine_and_bridge
    status = await bridge.handle_status(result.state.run_id)
    assert status["run_id"] == result.state.run_id
    assert status["status"] == "completed"
    assert status["progress"] == "1/1"


async def test_status_returns_error_for_unknown(engine_and_bridge):
    _, bridge, _ = engine_and_bridge
    status = await bridge.handle_status("nonexistent")
    assert "error" in status


async def test_status_shows_current_stage():
    async def slow_handler(prompt: str) -> str:
        return await good_handler(prompt)

    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=slow_handler),
    )
    workflow = Workflow(
        name="multi", version="1.0",
        stages=[
            Stage(id="a", name="A", skill="a", task="ta",
                  agents=[AgentRole(role="r", task="t")],
                  required_skills=[], optional_skills=[], methodology_skills=[]),
            Stage(id="b", name="B", skill="b", task="tb",
                  agents=[AgentRole(role="r", task="t")],
                  required_skills=[], optional_skills=[], methodology_skills=[]),
        ],
    )
    result = await engine.run("req", workflow)
    bridge = EngineMCPBridge(engine)
    status = await bridge.handle_status(result.state.run_id)
    assert status["current_stage"] == "b"


# ---------------------------------------------------------------------------
# handle_accept
# ---------------------------------------------------------------------------


async def test_accept_updates_status(engine_and_bridge):
    _, bridge, result = engine_and_bridge
    resp = await bridge.handle_accept(result.state.run_id)
    assert resp["status"] == "accepted"

    # Verify state changed
    state = bridge.engine.get_state(result.state.run_id)
    assert state.status == "accepted"


async def test_accept_returns_error_for_unknown(engine_and_bridge):
    _, bridge, _ = engine_and_bridge
    resp = await bridge.handle_accept("nonexistent")
    assert "error" in resp


# ---------------------------------------------------------------------------
# handle_reject
# ---------------------------------------------------------------------------


async def test_reject_updates_status(engine_and_bridge):
    _, bridge, result = engine_and_bridge
    resp = await bridge.handle_reject(result.state.run_id, "质量不达标")
    assert resp["status"] == "rejected"
    assert resp["reason"] == "质量不达标"

    # Verify state changed
    state = bridge.engine.get_state(result.state.run_id)
    assert state.status == "rejected"
    assert state.rejection_reason == "质量不达标"


async def test_reject_returns_error_for_unknown(engine_and_bridge):
    _, bridge, _ = engine_and_bridge
    resp = await bridge.handle_reject("nonexistent", "reason")
    assert "error" in resp


# ---------------------------------------------------------------------------
# handle_checkpoint_list
# ---------------------------------------------------------------------------


async def test_checkpoint_list_returns_checkpoints(tmp_path):
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
        checkpoint_dir=tmp_path / "checkpoints",
    )
    result = await engine.run("req", _make_workflow())
    bridge = EngineMCPBridge(engine)

    resp = await bridge.handle_checkpoint_list(result.state.run_id)
    assert "s1" in resp["checkpoints"]


async def test_checkpoint_list_empty():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    result = await engine.run("req", _make_workflow())
    bridge = EngineMCPBridge(engine)

    resp = await bridge.handle_checkpoint_list(result.state.run_id)
    assert resp["checkpoints"] == []


async def test_checkpoint_list_error_for_unknown():
    engine = WorkflowEngine(
        executor=StageExecutor(agent_handler=good_handler),
    )
    bridge = EngineMCPBridge(engine)
    resp = await bridge.handle_checkpoint_list("nonexistent")
    assert "error" in resp
