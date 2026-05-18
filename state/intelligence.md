---
name: workflow-intelligence
description: >
  Builds the V2 Java backend workflow intelligence: 8-scenario detection,
  dynamic profile selection, layer-based work item decomposition, dynamic
  checklist generation, compliance assessment, and evolution suggestions.
  Use when main-flow reaches Step 3 or the user asks for workflow intelligence.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# workflow-intelligence

Workflow Intelligence converts a natural-language Java backend requirement into
structured evidence that later planning and agent execution can consume.

## Mandatory Rules

- Keep `main-flow` as the orchestrator; this skill only supplies intelligence artifacts.
- Record every source capability as `v1`, `v2`, `v3`, or `deferred`.
- Use scenario confidence. Ask only when confidence is too low or top scenarios conflict.
- Select and record the guideline profile before creating work items.
- Generate checklists before any module is marked ready for implementation.
- Treat memory and evolution as contracts; do not silently patch skills, templates, or memory.
- Do not store secrets in intelligence artifacts.

## Flow

1. Read `01_prd_summary.md`, `02_spec_delta.md` when present, and `state.json`.
2. Run `workflow_intelligence_runner.py --run-dir <dir>` for base scenario, profile, items, checklists, compliance, and evolution.
3. Review scenario detection confidence. If < 0.7, ask user to confirm or adjust.
4. Review work item decomposition. Confirm layer assignments are correct.
5. Review checklists for completeness. Add project-specific items if needed.
6. Review compliance assessment and evolution proposals.
7. Update `state.json.workflow_intelligence`.

## Scenario Scope

V2 covers 8 Java backend scenarios:

- API/controller changes (java-api-change)
- Service logic changes (java-service-change)
- DAO/database changes (java-dao-change)
- Message/event changes (java-message-change)
- Scheduled task changes (java-task-change)
- Cache changes (java-cache-change)
- RPC changes (java-rpc-change)
- Test changes (java-test-change)

Performance, security, migration, documentation, and DDD scenarios are recognized as risk signals.

## Outputs

```text
WORKFLOW_INTELLIGENCE_STATUS: ready|blocked|failed
SCENARIO:
- <id, name, confidence, layers>
PROFILE:
- <profile, severity, ruleset>
WORK_ITEMS:
- <count, layers>
COMPLIANCE:
- <grade, risk, status>
ARTIFACTS:
- agent/scenario.json
- agent/profile.json
- agent/work_items.seed.json
- agent/checklists/<work-item-id>.json
- agent/compliance-report.json
- agent/evolution-report.json
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <action>
```
