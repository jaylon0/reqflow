---
name: verify-ui
description: >
  Verifies UI integration or interaction scenarios from an acceptance plan.
  Use when a requirement affects user-visible screens, frontend routes, or
  frontend-backend integration.
---

# verify-ui

Verify user-visible UI behavior.

## Mandatory Rules

- Prefer project-provided E2E or integration test commands.
- If no automation exists, produce a manual checklist.
- Do not treat screenshots alone as success unless the checklist requires human confirmation.

## Output Contract

```text
VERIFY_STATUS: success|failed|blocked|skipped
FAIL_STAGE: ui
FAILED_CASES:
- <case and reason>
SCREENSHOTS:
- <paths, if any>
ACTION_REQUIRED: <when blocked>
```
