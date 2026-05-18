from reqflow.runner.dashboard import Dashboard

def test_dashboard_init():
    dashboard = Dashboard(run_dir="/tmp/test-dashboard")
    assert dashboard.run_dir == "/tmp/test-dashboard"

def test_dashboard_format_status():
    dashboard = Dashboard(run_dir="/tmp/test-dashboard")
    status = {
        "run_id": "run-abc123",
        "config": "gpt",
        "adapter": "api_gpt",
        "current_stage": "verify",
        "completed_modules": ["analyze", "implement"],
        "steps_executed": 2,
        "step_statuses": {"analyze": "success", "implement": "success"},
        "checkpoints": 1,
        "memory_entries": 3,
    }
    output = dashboard.format_status(status)
    assert "run-abc123" in output
    assert "verify" in output
    assert "analyze" in output

def test_dashboard_format_trace():
    dashboard = Dashboard(run_dir="/tmp/test-dashboard")
    trace_data = {
        "spans": [
            {"name": "workflow", "duration_ms": 1500, "status": "success"},
            {"name": "step:analyze", "duration_ms": 500, "status": "success"},
            {"name": "step:implement", "duration_ms": 1000, "status": "success"},
        ]
    }
    output = dashboard.format_trace(trace_data)
    assert "workflow" in output
    assert "1500" in output
