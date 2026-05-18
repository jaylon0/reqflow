---
name: verify-api
description: >
  Verifies HTTP/API behavior from an acceptance plan or user-provided cases.
  Use when L3 work changes API behavior or when the user asks to verify an
  endpoint.
---

# verify-api

Verify API behavior with configured auth and base URL.

## Mandatory Rules

- Read cases from the acceptance plan when available.
- Do not guess credentials.
- If auth or base URL is missing, return `blocked` with action required.
- Report related files when failures can be mapped to source.

## Output Contract

```text
VERIFY_STATUS: success|failed|blocked|skipped
FAIL_STAGE: api
FAILED_CASES:
- <case and reason>
RELATED_FILES:
- <file paths>
ACTION_REQUIRED: <when blocked>
```
