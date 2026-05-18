---
name: evolution-proposal
description: >
  Creates a suggested evolution report after a Java backend run. Use after
  verification and compliance reporting to propose memory, context, checklist,
  skill, or template improvements without applying them automatically.
---

# evolution-proposal

Evolution Proposal is V1's safe self-improvement contract. It learns from a run
without silently mutating the plugin or persistent memory.

## Mandatory Rules

- Generate proposals only after there is execution, verification, or review
  evidence.
- Do not automatically patch skills, templates, memory, or guideline files.
- Separate global preferences from project-local knowledge.
- Separate confirmed lessons from hypotheses.
- Include source artifact paths for every proposal.
- Mark risky or low-confidence proposals as `needs-human`.

## Proposal Categories

- `global_preference`: user or team preference that may apply across projects.
- `project_knowledge`: architecture, call-chain, version, or workflow fact.
- `checklist_update`: repeated missing or useful checklist item.
- `context_pack_update`: context section that should be added or refreshed.
- `skill_update`: proposed SKILL.md rule or flow change.
- `template_update`: proposed run artifact or report template change.

## Outputs

```text
EVOLUTION_PROPOSAL_STATUS: ready|blocked|skipped
PROPOSALS:
- <category and count>
ARTIFACTS:
- agent/evolution-report.md
NEXT_ACTION:
- user confirmation before applying any proposal
```
