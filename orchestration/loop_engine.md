---
name: loop-engine
description: >
  Runs Requirement Flow repair and feedback loops for build failures, verification failures, review findings, blockers, and module-level implementation cycles. Use when main-flow, workflow-run, build, verify, review, or the user reports a failure, blocker, repeated error, broken check, or needs a controlled fix-verify-review loop.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# loop-engine

Controlled loop engine for development fallback. The goal is not to retry blindly; it is to turn failure signals into bounded repair.

## Mandatory Rules

- Always identify the loop trigger before patching.
- Preserve the smallest useful failure signal: command, stage, case, file, line, provider, and error summary.
- Classify the failure before editing.
- Restrict edits to the authorized module or files.
- Rerun the smallest check that can prove the fix.
- Stop on risk gates; do not broaden scope silently.
- Update `failure_fingerprints`, `current_loop_id`, and pending confirmation state when a run `state.json` exists.
- Write one loop artifact when inside a main-flow run.

## State Machine

```text
observe -> classify -> localize -> patch -> verify -> review -> decide
```

## Trigger Types

- `blocker`: user input or decision is missing.
- `build_failed`: build, lint, typecheck, or unit test failed.
- `verify_failed`: API, UI, message, RPC, task, data, log, or provider verification failed.
- `review_finding`: spec or standards review found a problem.
- `manual_feedback`: user reported an issue after a module or run.

## Failure Classification

Use exactly one primary class:

- `code_issue`
- `test_issue`
- `environment_issue`
- `requirement_unclear`
- `external_dependency`
- `provider_missing`
- `auth_missing`
- `data_missing`

## Risk Gates

Stop and ask the user when:

- the same fingerprint appears twice
- max retry count is reached
- the fix requires files outside the authorized module
- the requirement or expected behavior is unclear
- external auth, provider, data, or environment is unavailable
- a review finding requires product, API, architecture, or data-shape decision

Use `state.json` for these decisions when it exists:

- Increment `failure_fingerprints[<fingerprint>]` before deciding whether to retry.
- Compare the count to `max_retries`; repeated fingerprints must stop instead of looping blindly.
- Treat any patch outside `authorized_scope.modules` or `authorized_scope.files` as `needs-human`.
- Add unresolved questions to `pending_confirmations` and set `blocked_reason`.
- Clear `current_loop_id` only after the loop reaches `pass`, `blocked`, `needs-human`, or `aborted`.

## Loop Artifact

When a run directory exists, write:

```text
.dev-workflow/runs/<run-id>/loops/<loop-id>.md
```

Use `{pluginRoot}/templates/loop-record.template.md`.

Do not look for shared templates under `{baseDir}/templates`; this skill directory does not own a template folder.

The artifact must include the retry count, authorized scope, changed files, verification action, verification result, and whether a human decision is required.

## Output

```text
LOOP_STATUS: pass|retry|blocked|needs-human|aborted
LOOP_ID: <loop id or empty>
TRIGGER: blocker|build_failed|verify_failed|review_finding|manual_feedback
CLASSIFICATION: <primary class>
FINGERPRINT: <stable fingerprint>
PATCH_SCOPE:
- <files or modules>
VERIFY_ACTION:
- <command or manual check>
NEXT_ACTION:
- <why continuing or why stopped>
```
