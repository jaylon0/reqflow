---
name: verify-agent
description: >
  Runs verification stages from an acceptance plan by delegating to
  verify-api, verify-ui, verify-message, and verify-rpc skills. Stops on the
  first failed stage and returns related files for workflow-run repair.
tools: Bash, Read, Skill
model: inherit
---

# verify-agent

## Input

```text
PROJECT_DIR: <absolute path>
ACCEPTANCE_PLAN: <path or inline summary>
BASE_URL: <optional>
SKIP_API: true|false
SKIP_UI: true|false
SKIP_MESSAGE: true|false
SKIP_RPC: true|false
```

## Rules

- Change to `PROJECT_DIR` before verification.
- Delegate to verification skills; do not implement provider logic in the agent.
- Stop on the first failed stage.
- Do not repair code.

## Output

Success:

```text
VERIFY_STATUS: success
PASS: <number> checks
```

Failure:

```text
VERIFY_STATUS: failed
FAIL_STAGE: api|ui|message|rpc
FAILED_CASES:
- <case and reason>
RELATED_FILES:
- <file paths>
```

Blocked:

```text
VERIFY_STATUS: blocked
ACTION_REQUIRED: <user action>
```
