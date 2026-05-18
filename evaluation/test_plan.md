---
name: test-plan
description: >
  Creates an acceptance plan for a requirement. Use for L2 and L3 work, or
  when the user asks what should be tested or verified.
---

# test-plan

Generate an acceptance plan from the requirement, code changes, and project context.

## Mandatory Rules

- Mark data dependencies explicitly.
- Separate automated checks from manual checks.
- Prefer tests that reproduce the requested behavior or bug before implementation when practical.
- Do not invent provider capabilities. If a provider is missing, write a manual checklist item.
- Keep plans in the conversation by default. Write `.dev-workflow/acceptance-plan.md` only when workflow-run needs persistence or the user asks.

## Sections

Use this structure:

```markdown
# Acceptance Plan

## Requirement Summary
## Impacted Areas
## Automated Checks
## Manual Checks
## Data Dependencies
## External Provider Requirements
## Not Automated
```

## Test Strategy

- For bug fixes, include the smallest reproduction check first.
- For behavior changes, include at least one positive case and one relevant boundary or regression case when the project has a suitable test surface.
- For design-only or analysis-only work, state why no executable check is required.

## Diff Support

When generating an acceptance plan from code changes, use the generic diff script:

```bash
"{pluginRoot}/scripts/get_diff.sh" --base-branch main
```

Use `--diff-range HEAD~1..HEAD` when the user asks for the last commit only.

## Output Contract

```text
TEST_PLAN_STATUS: ready|blocked
TEST_PLAN_FILE: <path or empty>
CHECK_COUNT: <number>
MANUAL_CHECK_COUNT: <number>
ACTION_REQUIRED: <when blocked>
```
