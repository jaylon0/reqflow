---
name: requirement-router
description: >
  Classifies incoming work into Requirement Flow routing levels. Use when the
  user provides a PRD, issue, bug report, refactor request, screenshot-backed
  problem, or natural-language feature request; or when the user says
  "analyze only", "directly change it", "make a plan", "ship it",
  "run the full workflow", "需求", "实现", "修复", "只分析", "完整流程".
---

# requirement-router

Decide the delivery path before implementation.

## Mandatory Rules

- Respect explicit user intent: "only analyze", "do not edit", "directly change", "make a plan", "run full workflow".
- If risk is unclear, choose the safer higher level and explain why.
- Do not start external write operations from this skill.
- Do not require full project initialization before L0/L1 work.

## Routing Levels

| Level | Name | Default behavior |
|---|---|---|
| L0 | analyze-only | Inspect and explain only; no file edits |
| L1 | light-change | Implement local low-risk changes and run focused checks |
| L2 | planned-change | Present implementation and acceptance plan before edits |
| L3 | delivery-loop | Plan, implement, build, deploy/publish if configured, verify, and repair |

## L0 Triggers

- User asks for analysis, review, explanation, impact assessment, or debugging hypothesis.
- User explicitly says not to edit.
- Requirement is too ambiguous to plan safely.

## L1 Triggers

- Local low-risk edit: text, small style change, obvious bug, import/type fix, focused test fix, simple configuration adjustment.
- Expected blast radius is one or a few local files.
- No API, database, message, service contract, permission, release, or deployment impact.

## L2 Triggers

- Multi-file feature or refactor.
- Design tradeoffs exist.
- The work can be locally validated but does not require external delivery by default.
- Existing context is incomplete but enough to propose a plan.

## L3 Triggers

- API behavior or contract changes.
- Database schema, query, migration, persistence, or data consistency changes.
- Message/event/task/cron/RPC/service contract changes.
- Authentication, authorization, billing, security, release, deployment, package publishing, or external user-visible behavior.
- User explicitly asks to deploy, publish, release, verify, or run the full flow.

## Output Contract

Return a concise routing decision:

```text
ROUTE_LEVEL: L0|L1|L2|L3
REASON: <why this level fits>
REQUIRED_CONTEXT:
- <context needed now, if any>
NEXT_SKILL: workflow-run|context-bootstrap|none
USER_CONFIRMATION_REQUIRED: true|false
```
