"""Integration tests for hook executor, agent coordinator, and loop engine wiring in Engine."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import yaml

from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.hook_executor import HookExecutor
from reqflow.core.adapters.base import ModelResponse, TokenUsage


def _make_engine(tmp_path, workflow_yaml=None):
    """Create an Engine with an optional workflow YAML file."""
    run_dir = str(tmp_path / "test-run")
    workflows_dir = str(tmp_path / "workflows")
    os.makedirs(workflows_dir, exist_ok=True)
    if workflow_yaml:
        wf_path = Path(workflows_dir) / "test-wf.yaml"
        wf_path.write_text(yaml.dump(workflow_yaml), encoding="utf-8")
    config = RuntimeConfig(name="manual", display_name="Manual")
    return Engine(config=config, run_dir=run_dir, workflows_dir=workflows_dir)


def _mock_adapter():
    """Create a mock adapter that returns a successful ModelResponse."""
    adapter = MagicMock()
    adapter.name = "mock"
    adapter.call.return_value = ModelResponse(
        content="done",
        tokens=TokenUsage(input_tokens=10, output_tokens=5),
    )
    return adapter


# ─── Hook execution tests ────────────────────────────────────


def test_engine_executes_hooks_in_workflow(tmp_path):
    """Engine should call _execute_stage_hooks for steps that have knowledge_hooks."""
    workflow = {
        "stages": [
            {
                "name": "stage-with-hooks",
                "prompt": "do something",
                "knowledge_hooks": ["hook-a", "hook-b"],
            },
            {
                "name": "stage-no-hooks",
                "prompt": "do something else",
            },
        ],
    }
    engine = _make_engine(tmp_path, workflow)

    call_log = []

    async def mock_execute_stage_hooks(stage_def, context, trigger):
        call_log.append({
            "stage": stage_def.get("name"),
            "trigger": trigger,
            "hooks": stage_def.get("knowledge_hooks", []),
        })
        return {"status": "ok"}

    async def _run():
        adapter = _mock_adapter()
        with (
            patch.object(engine, "_execute_stage_hooks", side_effect=mock_execute_stage_hooks),
            patch.object(engine, "select_adapter", return_value=adapter),
        ):
            result = await engine.run_workflow_by_name("test-wf", "test requirement")
        return result

    result = asyncio.run(_run())

    # stage-with-hooks should have triggered before_stage and after_stage
    before_calls = [c for c in call_log if c["trigger"] == "before_stage"]
    after_calls = [c for c in call_log if c["trigger"] == "after_stage"]

    assert len(before_calls) == 1
    assert before_calls[0]["stage"] == "stage-with-hooks"
    assert before_calls[0]["hooks"] == ["hook-a", "hook-b"]

    assert len(after_calls) == 1
    assert after_calls[0]["stage"] == "stage-with-hooks"

    # stage-no-hooks should NOT trigger any hooks
    no_hook_calls = [c for c in call_log if c["stage"] == "stage-no-hooks"]
    assert len(no_hook_calls) == 0

    shutil.rmtree(str(tmp_path / "test-run"), ignore_errors=True)


def test_engine_hooks_failure_does_not_fail_step(tmp_path):
    """Hook failures should be logged as warnings, not fail the step."""
    workflow = {
        "stages": [
            {
                "name": "hooked-stage",
                "prompt": "do work",
                "knowledge_hooks": ["failing-hook"],
            },
        ],
    }
    engine = _make_engine(tmp_path, workflow)

    async def _run():
        adapter = _mock_adapter()
        with (
            patch.object(
                engine,
                "_execute_stage_hooks",
                side_effect=RuntimeError("hook exploded"),
            ),
            patch.object(engine, "select_adapter", return_value=adapter),
        ):
            result = await engine.run_workflow_by_name("test-wf", "requirement")
        return result

    result = asyncio.run(_run())
    # Step should still complete despite hook failure
    assert result["status"] == "completed"

    shutil.rmtree(str(tmp_path / "test-run"), ignore_errors=True)


# ─── Agent coordination loading tests ────────────────────────


def test_engine_loads_agent_coordination(tmp_path):
    """Engine._agent_coordinator should be set when a stage defines agent_coordination."""
    coord_config = {
        "dispatch": [
            {"type": "dev", "agent": "dev-agent"},
            {"type": "verify", "agent": "verify-agent"},
        ],
        "repair": {"max_rounds": 2},
    }
    workflow = {
        "stages": [
            {
                "name": "agent-stage",
                "prompt": "execute work",
                "agent_coordination": coord_config,
            },
        ],
    }
    engine = _make_engine(tmp_path, workflow)

    observed_coordinator = {}

    async def mock_run_workflow(workflow_steps, requirement):
        # Capture the coordinator during execution
        observed_coordinator["value"] = engine._agent_coordinator
        return {"steps": [], "status": "completed"}

    async def _run():
        with patch.object(engine, "run_workflow", side_effect=mock_run_workflow):
            await engine.run_workflow_by_name("test-wf", "test requirement")

    asyncio.run(_run())

    coordinator = observed_coordinator.get("value")
    assert coordinator is not None
    assert coordinator.dispatch_rules[0].agent == "dev-agent"
    assert coordinator.dispatch_rules[1].agent == "verify-agent"
    assert coordinator.max_repair_rounds == 2

    shutil.rmtree(str(tmp_path / "test-run"), ignore_errors=True)


def test_engine_agent_coordinator_cleared_after_run(tmp_path):
    """_agent_coordinator should be None after run_workflow_by_name completes."""
    workflow = {
        "stages": [
            {
                "name": "agent-stage",
                "prompt": "work",
                "agent_coordination": {"dispatch": [{"type": "dev", "agent": "a"}]},
            },
        ],
    }
    engine = _make_engine(tmp_path, workflow)

    async def _run():
        with patch.object(engine, "run_workflow", return_value={"steps": [], "status": "completed"}):
            await engine.run_workflow_by_name("test-wf", "req")

    asyncio.run(_run())
    assert engine._agent_coordinator is None

    shutil.rmtree(str(tmp_path / "test-run"), ignore_errors=True)


# ─── Loop engine loading tests ───────────────────────────────


def test_engine_loads_loop_engine(tmp_path):
    """Engine._loop_engine_instance should be set when definition has loop_engine."""
    loop_config = {
        "state_machine": "analyze -> fix -> verify",
        "max_iterations": 5,
        "risk_gates": ["max retry count reached"],
    }
    workflow = {
        "stages": [
            {"name": "loop-stage", "prompt": "work"},
        ],
        "loop_engine": loop_config,
    }
    engine = _make_engine(tmp_path, workflow)

    observed_loop = {}

    async def mock_run_workflow(workflow_steps, requirement):
        observed_loop["value"] = engine._loop_engine_instance
        return {"steps": [], "status": "completed"}

    async def _run():
        with patch.object(engine, "run_workflow", side_effect=mock_run_workflow):
            await engine.run_workflow_by_name("test-wf", "test requirement")

    asyncio.run(_run())

    loop_inst = observed_loop.get("value")
    assert loop_inst is not None
    assert loop_inst.max_iterations == 5
    assert loop_inst.states == ["analyze", "fix", "verify"]

    shutil.rmtree(str(tmp_path / "test-run"), ignore_errors=True)


def test_engine_loop_engine_cleared_after_run(tmp_path):
    """_loop_engine_instance should be None after run_workflow_by_name completes."""
    workflow = {
        "stages": [{"name": "s", "prompt": "p"}],
        "loop_engine": {"state_machine": "a -> b"},
    }
    engine = _make_engine(tmp_path, workflow)

    async def _run():
        with patch.object(engine, "run_workflow", return_value={"steps": [], "status": "completed"}):
            await engine.run_workflow_by_name("test-wf", "req")

    asyncio.run(_run())
    assert engine._loop_engine_instance is None

    shutil.rmtree(str(tmp_path / "test-run"), ignore_errors=True)


# ─── HookExecutor instance test ──────────────────────────────


def test_engine_has_hook_executor():
    """Engine should always have a HookExecutor instance."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-he-instance")
    assert isinstance(engine._hook_executor, HookExecutor)
    shutil.rmtree("/tmp/test-he-instance", ignore_errors=True)
