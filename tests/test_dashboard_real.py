import json
import os
import shutil
from pathlib import Path
from reqflow.runner.dashboard import Dashboard


def test_dashboard_shows_failed_status():
    """Dashboard should show failed stages, not just completed count."""
    run_dir = "/tmp/test-dashboard-real"
    os.makedirs(run_dir, exist_ok=True)
    try:
        state = {
            "run_id": "test-run",
            "current_stage": "stage2",
            "completed_modules": ["stage1"],
            "checkpoints": [],
            "memory": {"short_term": []},
        }
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        dashboard = Dashboard(run_dir=run_dir)
        status = {
            "run_id": "test-run",
            "config": "gpt",
            "adapter": "api_gpt",
            "current_stage": "stage2",
            "completed_modules": ["stage1"],
            "steps_executed": 2,
            "step_statuses": {"stage1": "success", "stage2": "failure"},
            "checkpoints": 0,
            "memory_entries": 0,
        }
        output = dashboard.format_status(status)
        assert "fail" in output.lower() or "FAIL" in output or "[FAIL]" in output
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
