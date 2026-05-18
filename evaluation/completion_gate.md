---
name: completion-gate
description: >
  Verifies that spec match, standards review, build, and required delivery
  checks have passed before main-flow reports completion.
---

# completion-gate

Completion verification gate.

This gate checks recorded evidence. It does not execute providers directly and must not invent verification results.

## Mandatory Rules

- Do not report completion until required checks are recorded in `08_verification.md`.
- Require spec match and standards match review results.
- Require manual checklist status when automated providers are unavailable.
- State missing verification as `BLOCKER`.
- Do not treat skipped provider checks as passed unless the user explicitly approved manual mode.

## Output

```text
COMPLETION_GATE_STATUS: pass|blocked|failed
REQUIRED_EVIDENCE:
- <artifact or command>
MISSING_EVIDENCE:
- <missing item or empty>
BLOCKERS:
- <blocker or empty>
```
