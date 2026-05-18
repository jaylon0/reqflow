---
description: Run or plan local and external verification for the current change.
argument-hint: "[check target]"
---

Choose the narrowest matching Requirement Flow skill for this request:

- `requirement-flow-plugin:build` for local build, test, lint, or typecheck checks.
- `requirement-flow-plugin:verify-api` for HTTP or API verification.
- `requirement-flow-plugin:verify-ui` for UI or browser verification.
- `requirement-flow-plugin:verify-message` for message, event, or job verification.
- `requirement-flow-plugin:verify-rpc` for service or RPC verification.

Input:

$ARGUMENTS

If the verification target is ambiguous, ask for the target using concrete options.
