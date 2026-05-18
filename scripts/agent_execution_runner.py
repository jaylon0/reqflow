#!/usr/bin/env python3
"""Validate seeded work items and create supervised agent execution contracts."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, load_state, read_text, save_state, update_section, utc_now, write_json, write_text


def validate_item(item: dict) -> list[str]:
    errors: list[str] = []
    if not item.get("id"):
        errors.append("missing id")
    if item.get("story_size") != "one supervised agent iteration":
        errors.append(f"{item.get('id', '<unknown>')} story_size must be one supervised agent iteration")
    if not item.get("acceptance_criteria"):
        errors.append(f"{item.get('id', '<unknown>')} acceptance_criteria is empty")
    return errors


def final_item(item: dict) -> dict:
    item_id = item["id"]
    return {
        "id": item_id,
        "title": item["title"],
        "scenario": item["scenario"],
        "task_type": item.get("task_type", "EXTEND"),
        "status": "pending",
        "priority": item.get("priority", 1),
        "story_size": item["story_size"],
        "authorized_scope": {"modules": [], "files": []},
        "context_pack": "agent/context-packs/java-context.md",
        "checklist": f"agent/checklists/{item_id}.json",
        "acceptance_criteria": item["acceptance_criteria"],
        "agent_ids": {"dev": "", "verify": "", "review": ""},
        "attempts": 0,
        "blockers": [],
        "evidence": [],
        "passes": False,
        "notes": item.get("notes", ""),
        "execution_record": {
            "dev_agent_id": "",
            "verify_agent_id": "",
            "review_agent_id": "",
            "repair_rounds": 0,
            "reports": {
                "dev": f"agent/reports/{item_id}/dev.json",
                "verify": f"agent/reports/{item_id}/verify.json",
                "review": f"agent/reports/{item_id}/review.json",
            },
        },
    }


def write_dispatch_log(run_dir: Path, action: str, agent_id: str, summary: str) -> None:
    """Append a timestamped line to agent/main-log.md."""
    log_path = run_dir / ARTIFACT_PATHS["agent_main_log"]
    timestamp = utc_now()
    existing = read_text(log_path, "# Agent Main Log\n")
    if "| Time |" not in existing:
        existing = existing.rstrip() + "\n\n| Time | Action | Agent | Summary |\n|---|---|---|---|"
    line = f"| {timestamp} | {action} | {agent_id} | {summary} |"
    write_text(log_path, existing.rstrip() + "\n" + line)


def update_item_status(run_dir: Path, item_id: str, status: str, report: dict | None = None) -> bool:
    """Update a single work item's status and optional execution record. Returns True if item found."""
    work_items_path = run_dir / ARTIFACT_PATHS["agent_work_items"]
    data = load_json(work_items_path, {"version": "work-items-v1", "items": []})
    found = False
    for item in data["items"]:
        if item["id"] == item_id:
            item["status"] = status
            if report:
                item.setdefault("execution_record", {}).update(report)
            found = True
            break
    write_json(work_items_path, data)
    return found


def _report_path(item_id: str, stage: str) -> str:
    return f"agent/reports/{item_id}/{stage}.json"


def write_report(run_dir: Path, item_id: str, stage: str, result: dict) -> None:
    """Write a JSON report to agent/reports/<item_id>/<stage>.json."""
    report_path = run_dir / _report_path(item_id, stage)
    write_json(report_path, result)


def create_repair_round(run_dir: Path, item_id: str, findings: list, round_num: int) -> None:
    """Record a repair round: update attempts, write repair report."""
    work_items_path = run_dir / ARTIFACT_PATHS["agent_work_items"]
    data = load_json(work_items_path, {"version": "work-items-v1", "items": []})
    for item in data["items"]:
        if item["id"] == item_id:
            item["attempts"] = round_num
            item.setdefault("execution_record", {})["repair_rounds"] = round_num
            break
    write_json(work_items_path, data)
    write_report(run_dir, item_id, f"repair-{round_num}", {"findings": findings, "round": round_num})


def init_work_item_execution(run_dir: Path, item_id: str) -> None:
    """Mark a work item as in_progress and create its report directory."""
    update_item_status(run_dir, item_id, "in_progress")
    report_dir = run_dir / f"agent/reports/{item_id}"
    report_dir.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    seed = load_json(run_dir / ARTIFACT_PATHS["agent_work_items_seed"], {"items": []})
    errors: list[str] = []
    for item in seed.get("items", []):
        errors.extend(validate_item(item))
    if not seed.get("items"):
        errors.append("agent/work_items.seed.json contains no items")

    if errors:
        update_section(
            state,
            "agent_execution",
            "blocked",
            [ARTIFACT_PATHS["agent_work_items_seed"]],
            [ARTIFACT_PATHS["agent_work_items_seed"]],
            errors,
            {"mode": "supervised_agents"},
        )
        save_state(run_dir, state)
        print("AGENT_EXECUTION_STATUS: blocked")
        return 1

    final_items = {"version": "work-items-v1", "items": [final_item(item) for item in seed["items"]]}
    write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], final_items)

    for item in final_items["items"]:
        report_dir = run_dir / f"agent/reports/{item['id']}"
        report_dir.mkdir(parents=True, exist_ok=True)

    write_text(
        run_dir / ARTIFACT_PATHS["agent_execution"],
        f"""# 07 Agent Execution

## Mode

- execution_mode: supervised_agents
- write_parallelism: serial
- read_parallelism: allowed
- autonomous_loop: reserved

## Work Items

- Count: {len(final_items['items'])}
- Path: {ARTIFACT_PATHS['agent_work_items']}

## Reports

- Path: agent/reports/<work-item-id>/

## BLOCKER

- None
""",
    )
    write_text(run_dir / ARTIFACT_PATHS["agent_main_log"], "# Agent Main Log\n\n- initialized supervised agent execution\n")
    update_section(
        state,
        "agent_execution",
        "complete",
        [ARTIFACT_PATHS["agent_execution"], ARTIFACT_PATHS["agent_work_items"], ARTIFACT_PATHS["agent_main_log"]],
        [ARTIFACT_PATHS["agent_work_items_seed"], ARTIFACT_PATHS["agent_execution"]],
        [],
        {
            "mode": "supervised_agents",
            "write_parallelism": "serial",
            "read_parallelism": "allowed",
            "autonomous_loop": "reserved",
            "current_work_item": final_items["items"][0]["id"],
            "repair_round": 0,
            "max_repair_rounds": 3,
        },
    )
    save_state(run_dir, state)
    print("AGENT_EXECUTION_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
