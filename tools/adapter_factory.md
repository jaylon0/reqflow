---
name: adapter-factory
description: >
  Generates project-local provider adapters from Requirement Flow templates.
  Use when the user wants to connect Git hosting, deployment, release,
  package publishing, container publishing, logs, databases, messages, RPC,
  auth, status checks, or a custom platform. The factory scans context,
  selects a template, creates or updates project adapter files, registers
  provider config, and validates adapter JSON structure.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# adapter-factory

Create project-local provider adapters without copying organization-specific platform logic into the plugin.

## Mandatory Rules

- Scan available project and provider context before asking.
- Use plugin templates as read-only sources.
- Generate adapters into the target project, not into the plugin template library.
- Do not write secrets to adapter files, provider config, or manifest files.
- Never overwrite an existing adapter automatically. Present a patch or candidate file and wait for confirmation.
- Run structure dry-run after generation: adapter must emit valid JSON with `status` equal to `success`, `failed`, `blocked`, or `skipped`.
- External write actions remain disabled unless workflow execution confirms them later.

## Supported Capabilities

| Capability | Purpose |
|---|---|
| `auth` | Provider auth and session checks |
| `git_host` | branch push, pull request, repository metadata |
| `deploy` | environment deployment and status |
| `release` | release creation and artifact publishing |
| `package_publish` | package registry publishing |
| `container_publish` | container image build and push |
| `log_query` | log lookup and error checks |
| `database_query` | read-only database validation |
| `message_trigger` | message, event, or job triggering |
| `rpc_invoke` | service invocation validation |
| `status` | generic provider status checks |
| `manual` | checklist-backed manual provider |

## Template Selection

Templates are read from the plugin root, not from this skill directory.

1. Prefer exact platform template: `{pluginRoot}/templates/adapters/<capability>/<platform>.py`.
2. Fall back to `{pluginRoot}/templates/adapters/<capability>/generic.py`.
3. If neither exists, use `{pluginRoot}/scripts/provider_adapter_stub.py` as a blocked adapter.

## Script

Use the factory script:

```bash
python3 "{pluginRoot}/scripts/adapter_factory.py" \
  --project-dir /path/to/project \
  --capability deploy \
  --platform vercel \
  --write
```

Without `--write`, the script prints a dry-run plan only.

## Generated Files

```text
.dev-workflow.example/adapters/<capability>/<platform>.py
.dev-workflow.example/adapters/adapter-manifest.yaml
.dev-workflow.example/providers.template.yaml
```

## Output Contract

```text
ADAPTER_FACTORY_STATUS: planned|generated|blocked|failed
ADAPTER_FILE: <path>
MANIFEST_FILE: <path>
PROVIDER_CONFIG: <path>
VALIDATION_STATUS: success|failed|blocked|skipped
ACTION_REQUIRED: <when blocked>
```
