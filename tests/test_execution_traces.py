import asyncio
import json
import shutil
from pathlib import Path
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_execution_log_includes_step_details():
    """agent_execution_log should include per-step details, not just workflow-level entry."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-exec-traces")

    async def mock_run_step(step, context=None):
        from reqflow.core.adapters.base import ModelResponse, TokenUsage
        response = ModelResponse(
            content=f"Result for {step['name']}",
            tool_calls=[],
            tokens=TokenUsage(input_tokens=100, output_tokens=50),
        )
        return StepResult(name=step["name"], status="success", response=response, duration_ms=200)

    engine.run_step = mock_run_step
    steps = [
        {"name": "analyze", "prompt": "analyze"},
        {"name": "implement", "prompt": "implement"},
    ]

    asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    state = json.loads((Path("/tmp/test-exec-traces") / "state.json").read_text())
    log = state["agent_execution_log"]

    # Should have workflow entry + per-step entries
    assert len(log) >= 3

    # Check per-step entries exist
    step_entries = [e for e in log if e.get("type") == "step"]
    assert len(step_entries) == 2
    assert step_entries[0]["step_name"] == "analyze"
    assert step_entries[0]["status"] == "success"
    assert "content_preview" in step_entries[0]

    shutil.rmtree("/tmp/test-exec-traces", ignore_errors=True)


def test_execution_log_includes_failure_evidence():
    """agent_execution_log should include error details for failed steps."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-exec-traces-fail")

    async def mock_run_step(step, context=None):
        if step["name"] == "fail_step":
            return StepResult(name="fail_step", status="failure", error="Connection refused", duration_ms=50)
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step
    steps = [
        {"name": "fail_step", "prompt": "fail"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))
    assert result["status"] == "failed"

    state = json.loads((Path("/tmp/test-exec-traces-fail") / "state.json").read_text())
    log = state["agent_execution_log"]

    step_entries = [e for e in log if e.get("type") == "step"]
    assert len(step_entries) == 1
    assert step_entries[0]["status"] == "failure"
    assert "Connection refused" in step_entries[0]["error"]

    shutil.rmtree("/tmp/test-exec-traces-fail", ignore_errors=True)
