#!/usr/bin/env python3
"""Run Requirement Flow loop-state regression scenarios in a temporary run."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


TERMINAL_STATUSES = {"pass", "blocked", "needs-human", "aborted"}


def decide_loop(state: dict, loop_id: str, fingerprint: str, changed_files: list[str], kind: str) -> dict:
    count = state["failure_fingerprints"].get(fingerprint, 0) + 1
    state["failure_fingerprints"][fingerprint] = count
    state["current_loop_id"] = loop_id

    allowed_files = set(state["authorized_scope"]["files"])
    out_of_scope = [path for path in changed_files if path not in allowed_files]
    if out_of_scope:
        status = "needs-human"
        reason = "outside authorized scope: " + ", ".join(out_of_scope)
    elif kind == "unclear_requirement":
        status = "needs-human"
        reason = "requirement unclear"
    elif count >= 2:
        status = "blocked"
        reason = "same fingerprint repeated"
    elif count >= state["max_retries"]:
        status = "blocked"
        reason = "max retry reached"
    else:
        status = "retry"
        reason = "bounded retry allowed"

    if status in {"blocked", "needs-human"}:
        state["pending_confirmations"].append(reason)
        state["blocked_reason"] = reason
    if status in TERMINAL_STATUSES:
        state["current_loop_id"] = ""

    result = {
        "loop_id": loop_id,
        "fingerprint": fingerprint,
        "attempts": count,
        "status": status,
        "reason": reason,
    }
    state["loops"].append(result)
    return result


def first_incomplete_module(state: dict) -> str:
    completed = set(state["completed_modules"])
    for module in state["planned_modules"]:
        if module["id"] not in completed:
            return module["id"]
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    state = json.loads((root / "templates/run-state.example.json").read_text())
    state.update({
        "run_id": "loop-state-regression",
        "current_step": 5,
        "step_status": "in_progress",
        "current_module": "api",
        "planned_modules": [
            {
                "id": "api",
                "name": "API",
                "status": "in_progress",
                "authorized_scope": {"modules": ["api"], "files": ["src/api.py"]},
            },
            {
                "id": "worker",
                "name": "Worker",
                "status": "pending",
                "authorized_scope": {"modules": ["worker"], "files": ["src/worker.py"]},
            },
        ],
        "completed_modules": [],
        "authorized_scope": {
            "modules": ["api"],
            "files": ["src/api.py"],
            "reason": "current module",
        },
    })

    with tempfile.TemporaryDirectory(prefix="rfp-loop-regression-") as tmp:
        run_dir = Path(tmp) / "runs" / state["run_id"]
        loops_dir = run_dir / "loops"
        loops_dir.mkdir(parents=True)

        results = [
            decide_loop(state, "loop-001", "build::api::E42", ["src/api.py"], "code_issue"),
            decide_loop(state, "loop-002", "build::api::E42", ["src/api.py"], "code_issue"),
            decide_loop(state, "loop-003", "review::schema-contract", ["src/schema.py"], "code_issue"),
            decide_loop(state, "loop-004", "prd::empty-state", ["src/api.py"], "unclear_requirement"),
        ]
        state["completed_modules"] = ["api"]
        next_module = first_incomplete_module(state)

        for result in results:
            (loops_dir / f"{result['loop_id']}.json").write_text(json.dumps(result, indent=2))
        (run_dir / "state.json").write_text(json.dumps(state, indent=2))

        checks = {
            "first_failure_retries": results[0]["status"] == "retry",
            "same_fingerprint_blocks": results[1]["status"] == "blocked",
            "out_of_scope_needs_human": results[2]["status"] == "needs-human",
            "unclear_requirement_needs_human": results[3]["status"] == "needs-human",
            "module_resume_order": next_module == "worker",
            "pending_confirmations_recorded": len(state["pending_confirmations"]) == 3,
            "loop_artifacts_written": len(list(loops_dir.glob("*.json"))) == 4,
        }

    status = "success" if all(checks.values()) else "failed"
    print(json.dumps({"status": status, "checks": checks, "results": results}, indent=2))
    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
