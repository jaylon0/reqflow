"""CLI fallback for host agent interaction via file protocol."""

from __future__ import annotations

import json
from pathlib import Path


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


def get_status(run_dir: str) -> dict:
    """Get the current run status."""
    state_file = Path(run_dir) / "state.json"
    if not state_file.exists():
        return {"error": f"State file not found: {state_file}"}
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"Cannot read state file: {e}"}
