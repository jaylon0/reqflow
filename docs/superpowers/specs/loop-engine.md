# Loop Engine

`loop-engine` is the common fallback loop for failed checks, review findings, blockers, and module-level repair.

It uses:

```text
observe -> classify -> localize -> patch -> verify -> review -> decide
```

The engine is intentionally bounded. It stops when the same failure repeats, the fix scope expands, retries are exhausted, or a human decision is required.

When a run has `state.json`, the loop uses it as the decision source:

- increment `failure_fingerprints[<fingerprint>]`
- compare retry count with `max_retries`
- restrict changes to `authorized_scope`
- record unresolved decisions in `pending_confirmations`
- update `current_loop_id` while the loop is active

## Loop Record

Inside a run, each loop writes a record under:

```text
.dev-workflow/runs/<run-id>/loops/<loop-id>.md
```

This keeps failed attempts, decisions, and verification evidence available for recovery.

Each record should include the failure fingerprint, previous attempts, authorized scope, changed files, verification result, and the human decision required when the loop cannot continue.

## Robustness Boundary

The loop engine protects local workflow state. It can retry bounded failures, stop repeated fingerprints, reject patches outside authorized scope, and preserve pending human decisions. It does not make external systems reliable by itself; provider login, deploy access, staging data, and remote verification still require project context or adapters.
