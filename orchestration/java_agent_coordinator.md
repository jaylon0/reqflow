---
name: java-agent-coordinator
description: >
  Creates the V1 Java module work-item and multi-agent execution contract. Use
  when main-flow has a Java backend implementation plan and needs work_items,
  agent handoff files, report paths, and controlled execution state.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# java-agent-coordinator

Java Agent Coordinator is the main-control contract for Java backend work items.
It coordinates state and handoff files. It does not directly edit business code.

## Mandatory Rules

- Do not write production source code from the coordinator role.
- Convert `05_impl_plan.md` into small work items that fit in one agent context.
- Each work item must have authorized scope, context pack path, checklist path,
  expected reports, acceptance criteria, and status.
- Keep write work serial in V1 and V2. Only read-only verify/review work may be
  parallelized later.
- Preserve context hygiene: pass paths and small summaries to agents, not full
  raw artifacts.
- Verify and review agents are read-only by default.
- Failed work should resume the same dev agent when the runtime supports resume;
  otherwise create a new repair handoff with the prior report paths.
- Update `state.json.agent_execution` and `agent/main-log.md` after every
  status change.

## Work Item States

Use exactly these states:

```text
pending | in_progress | pass | fail | blocked | low_quality_pass
```

`low_quality_pass` is allowed only after max repair rounds and must be recorded
as a risk in `agent/compliance-report.md`.

## Work Item Shape

```json
{
  "id": "wi-001",
  "module": "example-module",
  "scenario": "java-api-change",
  "status": "pending",
  "priority": 1,
  "authorized_scope": {
    "modules": [],
    "files": []
  },
  "context_pack": "agent/context-packs/wi-001.md",
  "checklist": "agent/checklists/wi-001.json",
  "acceptance_criteria": [],
  "agent_ids": {
    "dev": "",
    "verify": "",
    "review": ""
  },
  "reports": {
    "dev": "agent/reports/wi-001/dev-report.md",
    "verify": "agent/reports/wi-001/verify-report.md",
    "review": "agent/reports/wi-001/review-report.md"
  },
  "attempts": 0,
  "blockers": [],
  "evidence": []
}
```

## Outputs

```text
JAVA_AGENT_COORDINATOR_STATUS: ready|blocked|failed
CURRENT_WORK_ITEM: <id or empty>
ARTIFACTS:
- agent/work_items.json
- agent/main-log.md
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <action>
```
