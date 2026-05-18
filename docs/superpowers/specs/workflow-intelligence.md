# Workflow Intelligence

Workflow Intelligence is the V1 contract layer for Java backend delivery
automation. It does not replace `main-flow`; it gives `main-flow` durable
scenario, profile, checklist, context-pack, compliance, and evolution artifacts.

## Scope

V1 focuses on Java backend natural-language requirements:

- API or controller changes.
- Service logic changes.
- DAO, mapper, query, or database impacts.
- RPC, message, task, cache, search, or log verification impacts.
- Tests, build, review, and delivery verification.

Performance, security, migration, documentation, and DDD language tasks are V1
risk signals and later-version primary scenarios.

## Artifacts

Workflow Intelligence writes under `.dev-workflow/runs/<run-id>/agent/`:

```text
scenario.json
profile.json
work_items.seed.json
work_items.json
main-log.md
lessons-learned.md
context-packs/<work-item-id>.md
checklists/<work-item-id>.json
reports/<work-item-id>/
compliance-report.md
evolution-report.md
```

Unified Requirement Flow Runtime V1 uses a 10-stage artifact chain.
PCE-style workflow intelligence writes seed work items to `work_items.seed.json`.
Agent execution validates final work items and writes to `work_items.json`.
gstack/gbrain-style learning remains proposal-only in V1.

## Principles

- Matrix-driven: every borrowed capability must map to V1, V2, V3, or deferred.
- Self-contained: critical guideline, checklist, and report templates live in
  the plugin or the generated context pack.
- Contract first: V1 makes artifacts consumable by agents; V2 can automate
  supervised dispatch.
- Safe evolution: V1 writes proposals only and never patches skills, templates,
  or memory without user confirmation.

## Related Skills

- `workflow-intelligence`
- `java-agent-coordinator`
- `context-pack-builder`
- `dynamic-checklist`
- `compliance-report`
- `evolution-proposal`
