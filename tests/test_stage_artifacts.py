import asyncio
import json
import shutil
from pathlib import Path
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_stage_records_include_content():
    """stage_records should include the actual response content, not just metadata."""
    shutil.rmtree("/tmp/test-stage-artifacts", ignore_errors=True)
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-artifacts")

    async def mock_run_step(step, context=None):
        from reqflow.core.adapters.base import ModelResponse, TokenUsage
        response = ModelResponse(
            content=f"Output for {step['name']}: detailed analysis results here",
            tool_calls=[],
            tokens=TokenUsage(),
        )
        return StepResult(name=step["name"], status="success", response=response, duration_ms=100)

    engine.run_step = mock_run_step
    steps = [{"name": "analysis", "prompt": "analyze"}, {"name": "implementation", "prompt": "implement"}]

    asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    state = json.loads((Path("/tmp/test-stage-artifacts") / "state.json").read_text())
    assert len(state["stage_records"]) == 2

    first_record = state["stage_records"][0]
    assert first_record["name"] == "analysis"
    assert first_record["status"] == "success"
    assert "content" in first_record
    assert "detailed analysis" in first_record["content"]

    shutil.rmtree("/tmp/test-stage-artifacts", ignore_errors=True)


def test_stage_records_include_error_on_failure():
    """stage_records should include error details when step fails."""
    shutil.rmtree("/tmp/test-stage-artifacts-fail", ignore_errors=True)
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-artifacts-fail")

    async def mock_run_step(step, context=None):
        if step["name"] == "failing":
            return StepResult(name="failing", status="failure", error="API returned 401", duration_ms=50)
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step
    steps = [
        {"name": "failing", "prompt": "fail"},
        {"name": "after", "prompt": "after"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))
    assert result["status"] == "failed"

    state = json.loads((Path("/tmp/test-stage-artifacts-fail") / "state.json").read_text())
    fail_record = state["stage_records"][0]
    assert fail_record["status"] == "failure"
    assert "401" in fail_record["error"]

    shutil.rmtree("/tmp/test-stage-artifacts-fail", ignore_errors=True)
