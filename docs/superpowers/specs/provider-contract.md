# Provider Contract

Requirement Flow separates workflow orchestration from platform-specific execution.

## Provider Types

- `builtin`: common developer platforms supported by the plugin family.
- `custom`: a project or team script that implements the JSON adapter contract.
- `manual`: a checklist for human execution and confirmation.
- `generated`: a custom adapter produced from `adapter-factory` templates.

## Capabilities

Providers may implement one or more capabilities:

- `git_push`
- `pull_request`
- `release`
- `deploy`
- `package_publish`
- `container_publish`
- `log_query`
- `database_query`
- `message_trigger`
- `rpc_invoke`
- `auth_check`

## Custom Adapter Input

Custom adapters receive JSON on stdin:

```json
{
  "action": "deploy",
  "project_dir": "/path/to/project",
  "environment": "staging",
  "change": {
    "branch": "feature/example",
    "commit": "abc123",
    "files": ["src/example.ts"]
  },
  "context": {
    "base_url": "https://preview.example.com"
  }
}
```

Start from:

```bash
python3 requirement-flow-plugin/scripts/provider_adapter_stub.py
```

Or generate a project-local adapter:

```bash
python3 requirement-flow-plugin/scripts/adapter_factory.py \
  --project-dir . \
  --capability deploy \
  --platform vercel \
  --write
```

## Custom Adapter Output

Adapters must print JSON on stdout:

```json
{
  "status": "success",
  "artifacts": {
    "deploy_url": "https://preview.example.com",
    "run_url": "https://ci.example.com/runs/123"
  },
  "summary": "Deployment completed"
}
```

Allowed statuses:

- `success`
- `failed`
- `blocked`
- `skipped`

Failure example:

```json
{
  "status": "failed",
  "errors": [
    {
      "stage": "build",
      "message": "Build failed",
      "related_files": ["src/example.ts"]
    }
  ],
  "artifacts": {
    "run_url": "https://ci.example.com/runs/123"
  }
}
```

Blocked example:

```json
{
  "status": "blocked",
  "action_required": "Run the provider login command and retry",
  "missing_capability": "provider_auth"
}
```

## Confirmation Policy

External write actions require confirmation before execution:

- pushing branches
- creating pull requests
- creating releases
- deploying
- publishing packages
- pushing container images

Before asking for confirmation, show the platform, target, account when known, action, and risk.

## Secret Policy

Do not store credentials in project files. Use CLI sessions, environment variables, system keychains, or explicit user authorization.

## Generated Adapter Manifest

Generated adapters are registered in:

```text
.dev-workflow.example/adapters/adapter-manifest.yaml
```

The manifest records adapter name, capability, platform, template source, commands, external write actions, generation time, and whether the file is user maintained.
