---
description: Run or plan local and external verification for the current change.
argument-hint: "[check target]"
---

Choose the narrowest matching Requirement Flow skill for this request:

- `reqflow:build` for local build, test, lint, or typecheck checks.
- `reqflow:verify-api` for HTTP or API verification.
- `reqflow:verify-ui` for UI or browser verification.
- `reqflow:verify-message` for message, event, or job verification.
- `reqflow:verify-rpc` for service or RPC verification.

Input:

$ARGUMENTS

If the verification target is ambiguous, ask for the target using concrete options.
