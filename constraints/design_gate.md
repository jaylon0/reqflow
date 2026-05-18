---
name: design-gate
description: >
  Requires explicit approval before implementation for design-sensitive work,
  architecture choices, contracts, data shape, provider behavior, or module
  sequencing.
---

# design-gate

Design approval gate.

This gate records approval state only. It does not make architecture, contract, or data decisions by itself.

## Mandatory Rules

- Require user confirmation for technical plans that change architecture, API, data, messages, RPC, permissions, rollout, or provider behavior.
- Record approved decisions in the run artifact.
- Do not infer approval from silence.
- Treat unresolved design decisions as `BLOCKER`.

## Output

```text
DESIGN_GATE_STATUS: approved|blocked
APPROVED_DECISIONS:
- <decision>
BLOCKERS:
- <decision needed or empty>
```
