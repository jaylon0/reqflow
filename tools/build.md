---
name: build
description: >
  Runs local build, test, lint, or typecheck commands based on project
  context. Use when workflow-run or build-agent needs a focused local
  validation step.
---

# build

Run local validation without deploying.

## Mandatory Rules

- Prefer commands declared in `.dev-workflow/context.yaml`.
- If no command is configured, infer from project files before asking.
- Return structured status and concise errors.
- Do not fix code inside this skill; the orchestrator owns repair.
- When a check fails, preserve the failure signal needed for diagnosis instead of summarizing it away.

## Command Discovery

Common defaults:

| Project files | Candidate checks |
|---|---|
| `package.json` | `npm test`, `npm run build`, `npm run lint`, `npm run typecheck` if scripts exist |
| `pnpm-lock.yaml` | `pnpm test`, `pnpm build`, `pnpm lint` if scripts exist |
| `pom.xml` | `mvn test` or configured Maven command |
| `pyproject.toml` | configured test/build command |
| `go.mod` | `go test ./...` |
| `Makefile` | configured make target or `make test` |

## Script Support

Use the generic runner when available:

```bash
python3 "{pluginRoot}/scripts/run_checks.py" --project-dir /path/to/project --scope focused
python3 "{pluginRoot}/scripts/run_checks.py" --project-dir /path/to/project --scope full
```

Pass `--command "<command>"` to override detected checks.

## Output Contract

```text
BUILD_STATUS: success|failed|blocked|skipped
BUILD_TOOL: <tool or command>
ERRORS:
- <file:line message, when available>
ACTION_REQUIRED: <when blocked>
```

## Failure Handoff

Return enough detail for workflow-run to diagnose:

- command and working directory
- first failing test or task
- stable error fingerprint
- relevant file and line, when available
