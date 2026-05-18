import pytest
from reqflow.core.adapters.api import APIAdapter


def test_api_adapter_raises_on_http_error():
    """API adapter must raise RuntimeError on HTTP errors, not return error response."""
    adapter = APIAdapter(
        api_key="invalid-key",
        base_url="https://httpbin.org",
        model="gpt-4o",
        provider="openai",
    )
    with pytest.raises(RuntimeError, match="API call failed"):
        adapter.call(prompt="test")


import asyncio
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_engine_stops_on_step_failure():
    """Engine must stop workflow when a step fails, not continue to next steps."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-fail-fast")

    executed_steps = []

    async def mock_run_step(step, context=None):
        executed_steps.append(step["name"])
        if step["name"] == "step1":
            return StepResult(name="step1", status="failure", error="simulated failure")
        return StepResult(name=step["name"], status="success")

    engine.run_step = mock_run_step

    steps = [
        {"name": "step1", "prompt": "first"},
        {"name": "step2", "prompt": "second"},
        {"name": "step3", "prompt": "third"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    assert result["status"] == "failed"
    assert result["failed_at"] == "step1"
    assert "step2" not in executed_steps
    assert "step3" not in executed_steps

    import shutil
    shutil.rmtree("/tmp/test-fail-fast", ignore_errors=True)
