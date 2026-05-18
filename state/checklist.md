---
name: dynamic-checklist
description: >
  Generates V1 work-item checklists from Java backend scenario, guideline
  profile, severity, custom acceptance criteria, and project constraints. Use
  before implementation, review, verification, or compliance reporting.
---

# dynamic-checklist

Dynamic checklists bind scenario structure to coding discipline.

## Mandatory Rules

- Generate checklist items before a work item is marked implementation-ready.
- Separate `mandatory`, `important`, `nice_to_have`, and `info`.
- Include item source: scenario, profile, custom acceptance, project rule, or
  verification requirement.
- Deduplicate semantically equivalent items.
- If mandatory items conflict, mark the checklist `blocked` and record the
  conflict instead of choosing silently.

## V1 Inputs

```json
{
  "work_item_id": "wi-001",
  "scenario": "java-api-change",
  "profile": "standard-delivery",
  "severity": "balanced",
  "custom_acceptance_criteria": [],
  "project_constraints": []
}
```

## V1 Output Path

```text
agent/checklists/<work-item-id>.json
```

## Outputs

```text
DYNAMIC_CHECKLIST_STATUS: ready|blocked|failed
WORK_ITEM: <id>
MANDATORY_ITEMS: <count>
IMPORTANT_ITEMS: <count>
ARTIFACTS:
- agent/checklists/<work-item-id>.json
```
