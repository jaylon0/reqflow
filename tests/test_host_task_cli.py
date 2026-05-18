import json
import os
import shutil
import time
from pathlib import Path
from reqflow.runner.host_task import get_next_task, submit_result, get_status


def test_get_next_task_returns_packet():
    run_dir = "/tmp/test-host-task-cli"
    os.makedirs(run_dir, exist_ok=True)
    try:
        task = {"stage_id": "s1", "prompt": "do something"}
        (Path(run_dir) / "task.json").write_text(json.dumps(task))
        result = get_next_task(run_dir)
        assert result is not None
        assert result["stage_id"] == "s1"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_next_task_returns_none_when_no_task():
    run_dir = "/tmp/test-host-task-no-task"
    os.makedirs(run_dir, exist_ok=True)
    try:
        result = get_next_task(run_dir)
        assert result is None
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_submit_result_writes_result_json():
    run_dir = "/tmp/test-host-task-submit"
    os.makedirs(run_dir, exist_ok=True)
    try:
        result_data = {"status": "success", "summary": "done"}
        result_file = Path(run_dir) / "input-result.json"
        result_file.write_text(json.dumps(result_data))
        output = submit_result(run_dir, str(result_file))
        assert output["status"] == "ok"
        written = json.loads((Path(run_dir) / "result.json").read_text())
        assert written["status"] == "success"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_status_reads_state():
    run_dir = "/tmp/test-host-task-status"
    os.makedirs(run_dir, exist_ok=True)
    try:
        state = {"run_id": "test", "current_stage": "s1", "completed_modules": []}
        (Path(run_dir) / "state.json").write_text(json.dumps(state))
        status = get_status(run_dir)
        assert status["run_id"] == "test"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_status_shows_timeout_info():
    """get_status should indicate when a task has timed out."""
    run_dir = "/tmp/test-host-task-timeout"
    os.makedirs(run_dir, exist_ok=True)
    try:
        task = {"stage_id": "s1", "prompt": "do something", "created_at": time.time() - 300}
        (Path(run_dir) / "task.json").write_text(json.dumps(task))
        state = {"run_id": "test", "current_stage": "s1", "completed_modules": []}
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        status = get_status(run_dir)
        assert status.get("task_pending") is True
        assert status.get("task_timed_out") is True
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_status_no_timeout_for_recent_task():
    """get_status should not flag timeout for recent tasks."""
    run_dir = "/tmp/test-host-task-recent"
    os.makedirs(run_dir, exist_ok=True)
    try:
        task = {"stage_id": "s1", "prompt": "do something", "created_at": time.time() - 10}
        (Path(run_dir) / "task.json").write_text(json.dumps(task))
        state = {"run_id": "test", "current_stage": "s1", "completed_modules": []}
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        status = get_status(run_dir)
        assert status.get("task_pending") is True
        assert status.get("task_timed_out", False) is False
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
