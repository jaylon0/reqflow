import asyncio
import json
import shutil
from pathlib import Path
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_state_records_stage_details():
    """state.json should contain stage_records with per-stage status."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-records")

    async def mock_run_step(step, context=None):
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step
    steps = [{"name": "step1", "prompt": "first"}, {"name": "step2", "prompt": "second"}]

    asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    state = json.loads((Path("/tmp/test-stage-records") / "state.json").read_text())
    assert "stage_records" in state
    assert len(state["stage_records"]) == 2
    assert state["stage_records"][0]["name"] == "step1"
    assert state["stage_records"][0]["status"] == "success"

    shutil.rmtree("/tmp/test-stage-records", ignore_errors=True)
