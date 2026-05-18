#!/usr/bin/env python3
"""Archive a run and generate safe evolution proposals."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_state, save_state, update_section, write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    lessons = """# Lessons Learned

## Local Lessons

- Preserve source capability trace in workflow intelligence artifacts.
- Keep evolution proposals separate from automatic memory or skill writes.
"""
    evolution = """# Evolution Report

## Proposals

- Review whether repeated missing-provider verification entries should become configured providers.
- Review whether scenario/profile rules need project-specific additions.

## Safety

- No skill, template, memory, or global configuration changes were applied automatically.
"""
    archive = """# 10 Archive

## Archive Readiness

- Status: complete

## Spec Delta Application

- V1 records archive evidence only.

## Lessons

- Path: agent/lessons-learned.md

## Evolution Proposal

- Path: agent/evolution-report.md

## Result

- Status: complete

## BLOCKER

- None
"""
    write_text(run_dir / ARTIFACT_PATHS["agent_lessons"], lessons)
    write_text(run_dir / ARTIFACT_PATHS["agent_evolution"], evolution)
    write_text(run_dir / ARTIFACT_PATHS["archive"], archive)
    update_section(
        state,
        "archive",
        "complete",
        [ARTIFACT_PATHS["archive"], ARTIFACT_PATHS["agent_lessons"], ARTIFACT_PATHS["agent_evolution"]],
        [ARTIFACT_PATHS["verification"], ARTIFACT_PATHS["archive"]],
        [],
    )
    save_state(run_dir, state)
    print("ARCHIVE_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
