import json
import os
import shutil
from pathlib import Path
from reqflow.runner.dashboard import Dashboard


def test_dashboard_shows_stage_artifacts():
    """Dashboard should display stage content previews."""
    run_dir = "/tmp/test-dashboard-artifacts"
    os.makedirs(run_dir, exist_ok=True)
    try:
        state = {
            "run_id": "test-run",
            "current_stage": "done",
            "completed_modules": ["analysis", "implementation"],
            "checkpoints": [],
            "memory": {"short_term": []},
            "stage_records": [
                {"name": "analysis", "status": "success", "duration_ms": 100, "content": "Analyzed requirements and found 3 key points"},
                {"name": "implementation", "status": "failure", "duration_ms": 50, "error": "API 401", "content": ""},
            ],
        }
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        dashboard = Dashboard(run_dir=run_dir)
        status = {
            "run_id": "test-run",
            "config": "host",
            "adapter": "host",
            "current_stage": "done",
            "completed_modules": ["analysis", "implementation"],
            "steps_executed": 2,
            "step_statuses": {"analysis": "success", "implementation": "failure"},
            "checkpoints": 0,
            "memory_entries": 0,
            "stage_records": state["stage_records"],
        }
        output = dashboard.format_status(status)
        # Stage artifacts section should exist
        assert "Stage Artifacts" in output
        # Content preview should appear
        assert "Analyzed requirements" in output
        # Error should appear for failed stage
        assert "API 401" in output
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_dashboard_shows_timeout_recovery_info():
    """Dashboard should show recovery instructions when timeout detected."""
    run_dir = "/tmp/test-dashboard-recovery"
    os.makedirs(run_dir, exist_ok=True)
    try:
        dashboard = Dashboard(run_dir=run_dir)
        status = {
            "run_id": "test-run",
            "config": "host",
            "adapter": "host",
            "current_stage": "step2",
            "completed_modules": ["step1"],
            "steps_executed": 2,
            "step_statuses": {"step1": "success", "step2": "timeout"},
            "checkpoints": 0,
            "memory_entries": 0,
            "stage_records": [
                {"name": "step1", "status": "success", "duration_ms": 100},
                {"name": "step2", "status": "timeout", "duration_ms": 120000},
            ],
        }
        output = dashboard.format_status(status)
        # Should show TIMEOUT marker
        assert "TIMEOUT" in output
        # Should show recovery section
        assert "Recovery" in output
        assert "超时" in output
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
