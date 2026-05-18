---
name: main-flow
description: >
  Runs the full Requirement Flow PRD-to-code workflow with persistent artifacts, checkpoints, resumable state, module-level coding, review, and repair loops. Use when the user provides a PRD, larger requirement, multi-module change, cross-repository task, or asks for the complete flow, main-flow, full PRD-to-code workflow, or resumable development workflow.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# main-flow

Full PRD-to-code workflow for larger work. Keep `requirement-flow` as the lightweight route; use this skill only for explicit long-flow work.

## Mandatory Rules

- Create or resume a run under `.dev-workflow/runs/<run-id>/`.
- Read `state.json` and `memory.md` before continuing an existing run.
- Do not auto-switch branches. If recorded branch and current branch differ, show the difference and ask for confirmation.
- Stop at every checkpoint with unresolved BLOCKERs.
- Route failed checks, review findings, and module repair through `loop-engine`.
- Update `state.json` after every step, module, checkpoint, and loop decision.
- Derive the next module from `planned_modules` and `completed_modules`; do not infer module order from prose alone.
- Keep the current module's authorized scope in `state.json` before any module-level edit or loop.
- Never write secrets to run artifacts.
- Run spec governance before technical planning for durable behavior changes.
- Run Java context discovery before technical planning for Java backend work unless the change is L0 analysis-only or a trivial local edit.
- Run workflow intelligence for Java backend natural-language requirements before implementation planning.
- Do not claim graph, RAG, or impact evidence exists without a provider result or artifact reference.
- Run quality gates before module coding, review completion, and final completion.
- Treat V2 agent execution as supervised_agents mode unless the user explicitly asks for autonomous execution.
- Archive specs only after verification passes and the user confirms archive behavior.
- Keep `main-flow` as the user-facing orchestrator; do not embed runner implementation details in this skill.
- Use `workflow_intelligence_runner.py` for initial work item seeding and `agent_execution_runner.py` for final work item validation.
- Treat `autonomous_loop` as reserved. V1 uses `supervised_agents` or a manual contract fallback.
- Never auto-apply memory, skill, template, or global configuration changes from evolution proposals.

## Run Files

Each run owns:

```text
state.json
memory.md
01_prd_summary.md
02_spec_delta.md
03_workflow_intelligence.md
04_context_discovery.md
05_tech_plan.md
06_impl_plan.md
07_agent_execution.md
08_code_review.md
09_verification.md
10_archive.md
loops/<loop-id>.md
graph/
rag/
agent/
  scenario.json
  profile.json
  work_items.seed.json
  work_items.json
  main-log.md
  lessons-learned.md
  compliance-report.md
  evolution-report.md
  context-packs/
  checklists/
  reports/
```

Use plugin-root templates for structure:

- `{pluginRoot}/templates/run-state.example.json`
- `{pluginRoot}/templates/run-artifacts/`

Do not look for shared templates under `{baseDir}/templates`; this skill directory does not own a template folder.

`state.json` is the recovery contract. Keep these fields current:

- `planned_modules`: ordered module list copied from `05_impl_plan.md`.
- `completed_modules`: module ids that passed implementation, verification, and review.
- `authorized_scope`: modules and files allowed for the current step or loop.
- `failure_fingerprints`: retry counts keyed by stable failure fingerprint.
- `pending_confirmations`: unresolved product, API, architecture, data, provider, or scope decisions.
- `last_stable_step` and `last_stable_artifact`: the latest point safe to resume from.
- `change_id`: the current spec governance change id.
- `spec_status`: `draft`, `approved`, `archived`, or `blocked`.
- `context_engine`: graph and RAG status plus last graph/index versions.
- `quality_gates`: design, TDD, review, and verification gate status.
- `archive_status`: `not_started`, `ready`, `archived`, or `blocked`.
- `workflow_intelligence`: scenario, profile, checklist, compliance, and capability trace status.
- `agent_execution`: V1 contract mode, current work item, work item path, and repair round limit.
- `memory_contract`: global hint load status plus local lessons and evolution report paths.
- `current_scenario`, `guideline_profile`, `compliance_status`, and `evolution_status`.

## Flow

```text
0. Start or resume run
1. PRD understanding -> 01_prd_summary.md -> checkpoint
2. Spec governance -> 02_spec_delta.md -> checkpoint
3. Workflow intelligence -> 03_workflow_intelligence.md and agent/* intelligence artifacts
   - Run workflow_intelligence_runner.py for base artifacts
   - Review scenario confidence, work item decomposition, checklists
   - Generate compliance and evolution artifacts
4. Java context discovery -> 04_context_discovery.md and graph/rag/context-pack artifacts
5. Technical plan -> 05_tech_plan.md -> checkpoint
6. Implementation plan -> 06_impl_plan.md and agent/work_items.seed.json -> checkpoint
7. Agent execution -> 07_agent_execution.md and agent/work_items.json
   - Load agent-coordinator skill
   - For each work item: dispatch dev -> parallel verify+review -> repair if needed
   - Coordinator writes structured reports to agent/reports/<id>/
8. Code review -> 08_code_review.md (aggregate review agent results)
9. Delivery verification -> 09_verification.md
10. Archive and evolution -> 10_archive.md -> checkpoint
```

## Checkpoints

Ask for explicit confirmation before continuing when:

- PRD summary contains unresolved questions.
- Scenario detection or profile selection is ambiguous enough to change scope or verification.
- Spec delta changes durable behavior and needs approval.
- Technical plan chooses architecture, interface, data, provider, or component behavior.
- Database, cache, message, contract, schema, auth, permission, or external resource shape changes.
- A module is completed and needs human review before the next module.
- Archive applies spec changes into durable project specs.
- Evolution proposal would update memory, context, skills, templates, or guideline files.

Use `BLOCKER:` lines for missing information or decisions.

## Module Progression

When step 6 starts or resumes:

1. Read `planned_modules` from `state.json`.
2. Pick the first module id not listed in `completed_modules`.
3. Copy that module's authorized scope into top-level `authorized_scope`.
4. Run implementation, local verification, and review for that module.
5. Mark the module complete only after verification and review pass.
6. If a loop is needed, keep `current_module`, `authorized_scope`, and `current_loop_id` current before invoking `loop-engine`.

## Step 7: Agent Execution

1. Run agent_execution_runner.py to validate work_items.seed.json → work_items.json
2. Load agent-coordinator skill
3. For each work item with status pending:
   a. Dispatch dev agent (Agent tool, subagent_type=claude)
   b. On dev success → dispatch verify + review agents in parallel
   c. Evaluate results: all pass → mark pass; any fail → repair loop
   d. Repair: dispatch new dev agent with prior findings, max 3 rounds
4. After all items processed:
   - Run agent_execution_runner.py to validate final states
   - Write 07_agent_execution.md summary
   - Update state.json.agent_execution.status
5. If any items blocked/failed:
   - Write BLOCKER to pending_confirmations

## Step 3: Workflow Intelligence

1. Run `workflow_intelligence_runner.py --run-dir <dir>` for base scenario, profile, items, checklists, compliance, and evolution.
2. Load workflow-intelligence skill.
3. Review scenario detection:
   - If confidence < 0.7, ask user to confirm or adjust.
   - Confirm layers are correct for the requirement.
4. Review work item decomposition:
   - Confirm each item's layer assignment.
   - Add or merge items if needed.
5. Review checklists:
   - Verify mandatory items cover the requirement.
   - Add project-specific checks.
6. Review compliance and evolution artifacts.
7. Update state.json.workflow_intelligence.status.

## Technical Gap Check

In step 4, check these default dimensions and any project-configured additions:

- traffic or capacity expectation
- idempotency for writes, jobs, messages, and retries
- rollout, feature flag, or fallback strategy
- stability: dependency degradation, timeout, retry, rate limit, observability
- frontend/backend/API ownership and contract boundaries

Append conclusions to `04_tech_plan.md`; do not silently overwrite prior decisions.

## Knowledge Hooks

Use stage hooks from project context when present. Defaults:

- Step 2: `spec-governance`, `spec-delta`, `constitution-check`
- Step 3: `workflow-intelligence`, `dynamic-checklist`, `compliance-report`, `evolution-proposal`
- Step 4: `java-context-engine`, `java-code-graph`, `java-semantic-index`, `java-impact-analysis`, `context-pack-builder`
- Step 5: `infra-components`, `domain-components`, `support-infra-catalog`, `support-domain-rules`
- Step 6: `java-agent-coordinator`, `context-pack-builder`, `dynamic-checklist`
- Step 7: `java-agent-coordinator`, `agent-coordinator`, `context-pack-builder`, `dynamic-checklist`
- Step 8 before file edits: `quality-gates`, `tdd-gate`, plus relevant catalog or standards support skill
- Step 8 after file edits: `coding-standards` and relevant support checks
- Step 9: relevant verification skills, `compliance-report`, and `completion-gate`
- Step 10: `spec-archive`, `evolution-proposal`

## Output

```text
MAIN_FLOW_STATUS: initialized|in_progress|blocked|completed
RUN_ID: <run id>
CURRENT_STEP: <0-10>
CURRENT_MODULE: <module or empty>
ARTIFACTS:
- <path>
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <confirmation, input, or command needed>
```
