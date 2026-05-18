---
name: spec-governance
description: >
  Coordinates delta spec creation, constitution checks, clarification markers,
  and spec archive behavior. Use when main-flow reaches spec governance,
  technical plan approval, or final archive.
---

# spec-governance

Spec governance router.

## Mandatory Rules

- Keep requirement truth in specs and changes, not only in chat.
- Stop on unresolved clarification items that affect behavior, data, contracts, or scope.
- Use constitution checks before technical planning and before completion.
- Archive only after verification passes and the user confirms archive behavior.

## Flow

1. Use `spec-delta` to create or validate the change delta.
2. Use `constitution-check` to evaluate project non-negotiable rules.
3. Record unresolved questions as `BLOCKER`.
4. Use `spec-archive` only after completion gates pass.

## Output

```text
SPEC_GOVERNANCE_STATUS: draft|approved|blocked|archived
CHANGE_ID: <change id>
ARTIFACTS:
- <path>
BLOCKERS:
- <blocker or empty>
```
