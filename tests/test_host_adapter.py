import json
import os
import shutil
from pathlib import Path
from reqflow.core.adapters.host import HostAgentAdapter


def test_host_adapter_creates_task_packet():
    """Host adapter should create a task packet file."""
    run_dir = "/tmp/test-host-adapter"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir)
        packet = adapter.create_task_packet(
            stage_id="test-stage",
            stage_name="Test Stage",
            prompt="Do something",
            required_tools=["bash", "read_file"],
            expected_artifacts=["output.md"],
        )
        assert packet["stage_id"] == "test-stage"
        assert packet["required_tools"] == ["bash", "read_file"]
        assert (Path(run_dir) / "task.json").exists()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_returns_blocked_without_result():
    """Host adapter should return blocked when no result packet exists."""
    run_dir = "/tmp/test-host-no-result"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir)
        response = adapter.call(prompt="test")
        assert "blocked" in response.content.lower() or "task" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_consumes_result_packet():
    """Host adapter should consume result packet and return success."""
    run_dir = "/tmp/test-host-result"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir)
        result_packet = {
            "status": "success",
            "summary": "Task completed",
            "artifacts": ["output.md"],
            "files_changed": ["src/main.py"],
        }
        (Path(run_dir) / "result.json").write_text(json.dumps(result_packet))
        response = adapter.call(prompt="test")
        assert "success" in response.content.lower() or "completed" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
