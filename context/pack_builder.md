---
name: context-pack-builder
description: >
  Builds a compact Java backend context pack for one work item from PRD/spec,
  Java context discovery, version constraints, entry coverage, workflow overlay,
  reuse examples, and guideline profile evidence.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# context-pack-builder

Context packs are the handoff format for future Java module dev, verify, and
review agents. They are not broad project summaries; they are task-scoped
execution context.

## Mandatory Rules

- Build one context pack per work item.
- Prefer current module examples before project-wide examples.
- Include version constraints when they are known; if missing, record `unknown`
  rather than guessing.
- Include entry coverage for HTTP, RPC, message, task, cache, search, and log
  impact when relevant.
- Include workflow overlay: what must be read, what order to change, and what
  refreshes the pack.
- Include only enough code evidence for the work item. Large raw graph/RAG
  outputs stay in `graph/` and `rag/`.
- Do not claim graph or RAG evidence unless the provider or artifact exists.

## Required Sections

```markdown
# Context Pack: <work-item-id>

## Requirement
## Scenario And Profile
## Authorized Scope
## Architecture Context
## Entry Coverage
## Call Chain And Impact
## Version Constraints
## Reuse Examples
## Workflow Overlay
## Checklist And Acceptance
## Risks And Unknowns
```

## Outputs

```text
CONTEXT_PACK_STATUS: ready|blocked|manual|failed
WORK_ITEM: <id>
ARTIFACTS:
- agent/context-packs/<work-item-id>.md
BLOCKERS:
- <blocker or empty>
```
