---
name: deploy
description: >
  Executes deployment, release, package publishing, or manual delivery
  through configured providers. Use for L3 delivery-loop work after local
  validation passes.
---

# deploy

Run external delivery providers.

## Mandatory Rules

- Confirm every external write operation before execution.
- Check provider auth/capability before execution.
- Never write secrets to project files.
- Use custom adapter JSON contracts for unknown platforms.
- If automation is unavailable, return manual checklist mode.

## Built-In Provider Families

Supported skeleton families:

- GitHub: push branch, create pull request, create release.
- Deploy: Vercel and Render style preview or production deploy.
- Package: npm, PyPI, and Docker publish.

These providers must still verify local CLI login state before use.

## Custom Adapter

Read provider config from `.dev-workflow/providers.yaml`. For `type: custom`, call the configured command with JSON on stdin and parse JSON from stdout.

Use the adapter stub as a starting point:

```bash
python3 "{pluginRoot}/scripts/provider_adapter_stub.py"
```

## Output Contract

```text
DEPLOY_STATUS: success|failed|blocked|skipped
ARTIFACTS:
- <url or identifier>
ERRORS:
- <summary>
ACTION_REQUIRED: <when blocked>
```
