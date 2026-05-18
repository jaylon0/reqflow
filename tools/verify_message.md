---
name: verify-message
description: >
  Verifies message, event, job, or task behavior through configured providers
  or manual checklists.
---

# verify-message

Verify asynchronous behavior.

## Mandatory Rules

- Do not send messages or trigger jobs without explicit confirmation.
- Use configured provider adapters for message/task systems.
- If no provider exists, generate manual steps.

## Output Contract

```text
VERIFY_STATUS: success|failed|blocked|skipped
FAIL_STAGE: message
FAILED_CASES:
- <case and reason>
RELATED_FILES:
- <file paths>
ACTION_REQUIRED: <when blocked>
```
