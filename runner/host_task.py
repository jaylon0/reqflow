"""CLI fallback for host agent interaction via file protocol."""

from __future__ import annotations

import json
import time
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 120


def get_next_task(run_dir: str) -> dict | None:
    """Get the next task packet from the run directory."""
    task_file = Path(run_dir) / "task.json"
    if not task_file.exists():
        return None
    try:
        return json.loads(task_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def submit_result(run_dir: str, result_path: str) -> dict:
    """Submit a result packet to the run directory."""
    result_file = Path(result_path)
    if not result_file.exists():
        return {"status": "error", "error": f"Result file not found: {result_path}"}
    try:
        data = json.loads(result_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"status": "error", "error": f"Cannot read result file: {e}"}

    dest = Path(run_dir) / "result.json"
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return {"status": "ok", "written_to": str(dest)}


def get_status(run_dir: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Get the current run status with timeout detection."""
    state_file = Path(run_dir) / "state.json"
    if not state_file.exists():
        return {"error": f"State file not found: {state_file}"}
    try:
        status = json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"Cannot read state file: {e}"}

    # Check for pending task
    task_file = Path(run_dir) / "task.json"
    if task_file.exists():
        try:
            task_data = json.loads(task_file.read_text())
            status["task_pending"] = True
            created_at = task_data.get("created_at", 0)
            if created_at and (time.time() - created_at) > timeout_seconds:
                status["task_timed_out"] = True
                status["timeout_seconds"] = timeout_seconds
        except (json.JSONDecodeError, OSError):
            pass

    return status
