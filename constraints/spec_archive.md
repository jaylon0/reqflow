---
name: spec-archive
description: >
  Archives approved delta specs into durable project specs after verification.
  Use when main-flow reaches the archive stage or when the user asks to archive
  a completed change.
---

# spec-archive

Spec archive gate.

## Mandatory Rules

- Archive only after completion verification passes.
- Show the requirements and scenarios that will be added, modified, or removed.
- Stop on conflicting requirement headers or scenario ownership.
- Do not delete run artifacts.
- Require user confirmation before applying archive changes.

## Output

```text
SPEC_ARCHIVE_STATUS: ready|archived|blocked|failed
UPDATED_SPECS:
- <path>
CONFLICTS:
- <conflict or empty>
BLOCKERS:
- <blocker or empty>
```
