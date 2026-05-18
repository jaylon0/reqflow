import json
import os
import shutil
import time
from pathlib import Path
from reqflow.core.adapters.host import HostAgentAdapter


def test_host_adapter_detects_timeout():
    """Host adapter should detect when task.json has been waiting too long."""
    run_dir = "/tmp/test-host-timeout"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir, timeout_seconds=1)
        # First call creates task.json
        adapter.call(prompt="test task")
        # Wait past timeout
        time.sleep(1.5)
        # Second call should detect timeout
        response = adapter.call(prompt="test task")
        assert "timeout" in response.content.lower() or "超时" in response.content
        assert response.raw.get("status") == "timeout"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_resume_after_timeout():
    """Host adapter should allow resume after timeout by accepting new result."""
    run_dir = "/tmp/test-host-resume"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir, timeout_seconds=1)
        # Create task and wait for timeout
        adapter.call(prompt="test task")
        time.sleep(1.5)
        adapter.call(prompt="test task")  # triggers timeout

        # Now submit a result (resume)
        result_data = {"status": "success", "summary": "recovered"}
        (Path(run_dir) / "result.json").write_text(json.dumps(result_data))

        # Next call should consume the result
        response = adapter.call(prompt="test task")
        assert "success" in response.content.lower() or "recovered" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_creates_recovery_info_on_timeout():
    """On timeout, host adapter should write recovery info to task.json."""
    run_dir = "/tmp/test-host-recovery-info"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir, timeout_seconds=1)
        adapter.call(prompt="test task")
        time.sleep(1.5)
        adapter.call(prompt="test task")

        task_file = Path(run_dir) / "task.json"
        task_data = json.loads(task_file.read_text())
        assert "timeout_at" in task_data or "recovery" in task_data
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
