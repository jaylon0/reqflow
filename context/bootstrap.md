---
name: context-bootstrap
description: >
  Scans the current project and creates or updates Requirement Flow context
  only when needed. Use when workflow-run lacks language, framework,
  build/test commands, provider configuration, standards, or domain catalog
  information.
---

# context-bootstrap

Build the minimum context needed for the current routing level.

## Mandatory Rules

- Scan before asking. Do not ask for information discoverable from project files.
- Do not require complete initialization for L0/L1 work.
- For unfamiliar code areas, identify the subsystem, neighboring patterns, and existing domain language before recommending changes.
- Do not store secrets in project files.
- Keep runtime context separate from shareable templates.

## Scan Targets

Look for common sources:

```text
README*
AGENTS.md / CLAUDE.md / CONTEXT.md
docs/adr/ / docs/architecture/ / docs/agents/
package.json
pnpm-lock.yaml / yarn.lock / package-lock.json
pom.xml / build.gradle / Makefile
pyproject.toml / requirements.txt
go.mod
Dockerfile / docker-compose.yml
.github/workflows/
vercel.json / netlify.toml / render.yaml / fly.toml
```

## Script Support

Use the generic scanner when available:

```bash
python3 "{pluginRoot}/scripts/project_scan.py"
```

Set `PROJECT_DIR=/path/to/project` to scan another project directory.

## Runtime Context

Write local runtime context only when implementation is authorized:

```text
.dev-workflow/context.yaml
.dev-workflow/providers.yaml
.dev-workflow/acceptance-plan.md
```

## Shareable Templates

Create examples when requested:

```text
.dev-workflow.example/context.template.yaml
.dev-workflow.example/providers.template.yaml
.dev-workflow.example/standards/
.dev-workflow.example/domain-catalog/
```

## Minimum Context by Level

| Level | Required context |
|---|---|
| L0 | Project can be read |
| L1 | Language/framework guess and focused check command if discoverable |
| L2 | L1 context plus relevant standards or local patterns |
| L3 | L2 context plus provider capability or manual checklist |

## Context Quality

- Capture only context needed for the selected route.
- Prefer existing project standards, ADRs, agent docs, and examples over generic defaults.
- If a project has no shared standards or domain catalog, continue with discovered local patterns instead of blocking the workflow.
