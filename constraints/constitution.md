---
name: constitution-check
description: >
  Checks project-level non-negotiable rules before planning, coding, review,
  and completion. Use when main-flow needs Spec-Kit-style constitution gating
  or when a change may violate project principles.
---

# constitution-check

Project constitution gate.

## Mandatory Rules

- Read `.dev-workflow/constitution.md` when it exists.
- If no project constitution exists, use `templates/constitution.template.md` as guidance and record `manual` status.
- Stop on violations that affect data safety, contracts, security, external writes, or architecture boundaries.
- Do not weaken constitution rules without explicit user confirmation.

## Output

```text
CONSTITUTION_STATUS: pass|manual|blocked|failed
CHECKS:
- <rule and result>
VIOLATIONS:
- <violation or empty>
BLOCKERS:
- <blocker or empty>
```
