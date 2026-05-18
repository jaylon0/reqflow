#!/usr/bin/env python3
"""Generate V1 spec governance artifacts for a Requirement Flow run."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_state, read_text, requirement_text, save_state, update_section, write_text


def build_spec_delta(run_dir: Path) -> str:
    prd = read_text(run_dir / ARTIFACT_PATHS["prd_summary"], "")
    requirement = requirement_text(run_dir).strip() or "Requirement from 01_prd_summary.md"
    blocker = "None" if prd.strip() else "Missing 01_prd_summary.md content"
    status = "ready" if blocker == "None" else "blocked"
    return f"""# 02 Spec Delta

## Change

{requirement}

## Affected Capabilities

- Java backend delivery
- Requirement Flow runtime

## ADDED Requirements

### Requirement: Preserve requested behavior through implementation
#### Scenario: Requirement is implemented and verified
- Given the approved requirement summary
- When the runtime proceeds through planning, execution, and verification
- Then artifacts and state must preserve traceable acceptance evidence

## MODIFIED Requirements

- None

## REMOVED Requirements

- None

## Clarifications

- None

## Constitution Checks

- Status: {status}
- Evidence: local V1 spec governance runner

## Approval

- Status: draft
- Approved by:
- Approved at:

## BLOCKER

- {blocker}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    content = build_spec_delta(run_dir)
    write_text(run_dir / ARTIFACT_PATHS["spec_delta"], content)
    blocked = "Missing 01_prd_summary.md content" in content
    update_section(
        state,
        "spec_governance",
        "blocked" if blocked else "complete",
        [ARTIFACT_PATHS["spec_delta"]],
        [ARTIFACT_PATHS["prd_summary"], ARTIFACT_PATHS["spec_delta"]],
        ["Missing 01_prd_summary.md content"] if blocked else [],
    )
    save_state(run_dir, state)
    print("SPEC_GOVERNANCE_STATUS:", state["spec_governance"]["status"])
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
