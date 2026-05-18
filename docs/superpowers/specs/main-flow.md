# Main Flow

`main-flow` is the full PRD-to-code workflow for larger requirements.

Use it when the task needs structured PRD understanding, code discovery, technical planning, module-level implementation, review, recovery, or cross-session continuation.

## Runtime Layout

```text
.dev-workflow/runs/<run-id>/
```

Each run contains `state.json`, `memory.md`, fixed step artifacts, and loop records.
For Java backend V1 workflow-intelligence runs, each run also contains an
`agent/` directory for scenario, profile, work-item, checklist, context-pack,
report, compliance, and evolution artifacts.

`state.json` is the source of truth for recovery:

- `planned_modules` defines the module order from the implementation plan.
- `completed_modules` defines which modules are finished.
- `authorized_scope` defines the files or modules that the current step may change.
- `failure_fingerprints` tracks retry counts for loop decisions.
- `pending_confirmations` records unresolved human decisions.
- `last_stable_step` and `last_stable_artifact` record the safest resume point.
- `workflow_intelligence` records scenario, profile, checklist, compliance, and
  capability trace status.
- `agent_execution` records V1 contract mode, current work item, and repair
  limits.
- `memory_contract` records local lessons and evolution proposal paths.

## Recovery

When `main-flow` starts, it should look for resumable runs. If one exists, show:

- run id
- current step
- current module
- blockers
- recorded branches
- next action

If the recorded branch differs from the current branch, ask before switching or continuing.

For implementation recovery, resume the first item in `planned_modules` that is not present in `completed_modules`. Do not guess module order from `06_coding.md`.

## Checkpoints

`main-flow` must stop for unresolved BLOCKERs and high-risk confirmations. It should not guess through missing product, architecture, data, provider, or contract decisions.

When a checkpoint blocks progress, write the decision needed to `pending_confirmations` and keep `blocked_reason` short enough to show in status output.

## Unified Java Backend Flow

For Java backend work, `main-flow` expands the run from the legacy PRD-to-code
sequence into a 01-10 sequence:

1. PRD summary.
2. Spec delta.
3. Workflow intelligence: 8-scenario detection, dynamic profiles, layer-based
   work item decomposition, dynamic checklists, compliance assessment, and
   evolution suggestions.
4. Context discovery through Java graph and semantic retrieval.
5. Technical plan.
6. Implementation plan and work-item decomposition.
7. Agent execution: coordinator dispatches dev, verify, and review subagents
   for each work item. Repair loop (max 3 rounds) with new agent dispatch on
   failure. Reports written to agent/reports/<item-id>/.
8. Code review.
9. Delivery verification and compliance report.
10. Archive and evolution proposal.

Unified Requirement Flow Runtime V1 uses a 10-stage artifact chain.
PCE-style workflow intelligence writes seed work items.
Agent execution validates final work items and uses supervised_agents mode.
gstack/gbrain-style learning remains proposal-only in V1.

The flow may run in manual mode when graph, semantic, deploy, or verification
providers are not configured. Manual mode must record missing provider evidence
instead of pretending automation succeeded.
