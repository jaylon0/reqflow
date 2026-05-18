---
name: spec-delta
description: >
  Creates and validates OpenSpec-style delta specifications with ADDED,
  MODIFIED, and REMOVED requirements. Use when a requirement changes durable
  behavior or when main-flow reaches the spec delta stage.
---

# spec-delta

Delta specification support.

## Mandatory Rules

- Use `ADDED Requirements`, `MODIFIED Requirements`, and `REMOVED Requirements`.
- Each requirement must include at least one scenario when behavior is user-observable or externally verifiable.
- Do not copy complete future-state specs for existing capabilities when a delta is sufficient.
- Mark ambiguous behavior as clarification or `BLOCKER`.
- Do not archive from this skill.

## Output

```text
SPEC_DELTA_STATUS: draft|valid|blocked
CHANGED_REQUIREMENTS:
- <requirement>
CLARIFICATIONS:
- <question or empty>
BLOCKERS:
- <blocker or empty>
```
