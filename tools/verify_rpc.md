---
name: verify-rpc
description: >
  Verifies service-to-service or RPC-style behavior through configured
  provider adapters or manual checklists.
---

# verify-rpc

Verify service invocation behavior.

## Mandatory Rules

- Do not guess service names, method names, or request schemas.
- Use configured provider adapters when available.
- If a provider is missing, produce manual verification steps.

## Output Contract

```text
VERIFY_STATUS: success|failed|blocked|skipped
FAIL_STAGE: rpc
FAILED_CASES:
- <case and reason>
RELATED_FILES:
- <file paths>
ACTION_REQUIRED: <when blocked>
```
