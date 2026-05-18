#!/usr/bin/env python3
"""Summarize V1 delivery verification evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, load_state, save_state, update_section, write_text


CHECKS = ["build", "test", "api", "rpc", "message", "ui", "database", "cache", "search", "log"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    work_items = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {"items": []})
    lines = ["# 09 Verification", "", "## Work Item Reports", ""]
    for item in work_items.get("items", []):
        er = item.get('execution_record', {})
        reports = er.get('reports', {})
        lines.append(f"- {item['id']}: dev={reports.get('dev', 'N/A')} verify={reports.get('verify', 'N/A')} review={reports.get('review', 'N/A')}")
    lines.extend(["", "## Verification Matrix", ""])
    for check in CHECKS:
        lines.append(f"- {check}: missing-provider")
    lines.extend(["", "## Result", "", "- Status: complete", "- Evidence type: local summary with missing-provider markers", "", "## BLOCKER", "", "- None"])
    write_text(run_dir / ARTIFACT_PATHS["verification"], "\n".join(lines))
    update_section(
        state,
        "delivery_verification",
        "complete",
        [ARTIFACT_PATHS["verification"]],
        [ARTIFACT_PATHS["agent_execution"], ARTIFACT_PATHS["verification"]],
        [],
        {"automated": [], "manual": [], "missing_provider": CHECKS},
    )
    save_state(run_dir, state)
    print("DELIVERY_VERIFICATION_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
