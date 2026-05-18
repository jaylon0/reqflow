---
name: workflow-run
description: >
  Orchestrates requirement-to-delivery work after requirement-router chooses
  a path. It scans context, plans complex work, delegates build/deploy/verify
  to agents or skills, supports manual provider checklists, and runs repair
  loops for failed checks. Use when a requirement is ready for implementation
  or when the user asks to "run requirement flow", "ship", "deliver",
  "build deploy verify", or "完整流程".
---

> `{baseDir}` means this skill directory.

# workflow-run

Main orchestration skill for Requirement Flow.

## Mandatory Rules

- Main context owns routing, user interaction, state tracking, and code repair.
- Long-running or noisy build/deploy/verify steps should be delegated to agents when available.
- Clarify only high-impact unknowns that change route, scope, provider target, or acceptance criteria.
- External write operations require explicit user confirmation with target, account, action, and risk.
- Secrets must not be written to project files.
- If automated providers are missing, switch to manual checklist mode rather than pretending delivery is complete.
- Stop automatic repair when the same failure fingerprint appears twice.
- For failed checks, review findings, blockers, or repeated errors, use `loop-engine` rather than ad hoc retry.

## Flow

```text
1. Route requirement
2. Bootstrap only required context
3. Zoom out when the affected subsystem or design boundary is unclear
4. For L0: analyze and stop
5. For L1: implement local change and run focused checks
6. For L2: present plan, wait for confirmation, implement and verify locally
7. For L3: present plan, implement, build, deploy/publish if configured, verify, repair failures
```

## Execution Methods

- Prefer test-first implementation when the acceptance behavior can be expressed as a focused unit, integration, API, or UI check.
- For bugs, regressions, and failed checks, reproduce first, minimize the failing case, form a hypothesis, instrument only as needed, then repair.
- For design-sensitive work, prototype or compare approaches only when the decision would materially change the implementation.
- Before final status for L2/L3, perform a lightweight review on two axes: requirement match and coding-standard fit.

## Context

Read project context from `.dev-workflow/context.yaml` when present. If missing or incomplete, use `context-bootstrap` to scan the project and ask only for required fields.

Runtime files belong in `.dev-workflow/` and should be ignored by source control. Shareable templates belong in `.dev-workflow.example/`.

## L3 Provider Handling

Before external actions:

1. Run provider capability checks.
2. Show the intended action and target.
3. Ask for confirmation.
4. Execute the built-in provider or custom adapter.
5. Parse the standard result.

Provider result statuses:

```text
success | failed | blocked | skipped
```

`blocked` requires user action, such as logging in or configuring a provider.

## Repair Loop

Prefer `loop-engine` for full repair records. For lightweight runs, follow the same bounded loop.

For build or verification failures:

```text
retry = 0
while retry < max_retries:
  compute failure fingerprint
  if same as previous fingerprint:
    stop and ask for user help
  fix related source files
  rerun required checks
  if checks pass:
    stop successfully
  retry += 1
```

Default `max_retries` is 3 unless configured.

## References

- `references/context-files.md`
- `references/routing-levels.md`
- `references/manual-mode.md`
